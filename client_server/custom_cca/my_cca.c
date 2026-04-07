// SPDX-License-Identifier: GPL-2.0-only
/*
 * Standalone Reno-style TCP congestion control module with pr_info logging
 * for tracking congestion window changes.
 */

#define pr_fmt(fmt) "TCP: " fmt

#include <linux/module.h>
#include <net/tcp.h>

static const char *my_cca_ca_state_name(u8 state)
{
	switch (state) {
	case TCP_CA_Open:
		return "Open";
	case TCP_CA_Disorder:
		return "Disorder";
	case TCP_CA_CWR:
		return "CWR";
	case TCP_CA_Recovery:
		return "Recovery";
	case TCP_CA_Loss:
		return "Loss";
	default:
		return "Unknown";
	}
}

static const char *my_cca_event_name(enum tcp_ca_event event)
{
	switch (event) {
	case CA_EVENT_TX_START:
		return "TX_START";
	case CA_EVENT_CWND_RESTART:
		return "CWND_RESTART";
	case CA_EVENT_COMPLETE_CWR:
		return "COMPLETE_CWR";
	case CA_EVENT_LOSS:
		return "LOSS";
	case CA_EVENT_ECN_NO_CE:
		return "ECN_NO_CE";
	case CA_EVENT_ECN_IS_CE:
		return "ECN_IS_CE";
	default:
		return "UNKNOWN_EVENT";
	}
}

static void my_cca_log_socket_state(const struct sock *sk, const char *reason)
{
	const struct tcp_sock *tp = tcp_sk(sk);
	const struct inet_sock *inet = inet_sk(sk);
	__be32 dest_ip = inet->inet_daddr;
	__be16 dest_port = inet->inet_dport;

	pr_info(
		"my_cca: %s cwnd=%u ssthresh=%u snd_cwnd_cnt=%u ca_state=%s(%u) in_slow_start=%u cwnd_limited=%u Destination: %pI4:%d\n",
		reason,
		tcp_snd_cwnd(tp),
		tp->snd_ssthresh,
		tp->snd_cwnd_cnt,
		my_cca_ca_state_name(inet_csk(sk)->icsk_ca_state),
		inet_csk(sk)->icsk_ca_state,
		tcp_in_slow_start(tp),
		tcp_is_cwnd_limited(sk),
		&dest_ip,
		ntohs(dest_port));
}

/* Slow start is used when cwnd is no greater than ssthresh. */
static u32 my_cca_slow_start(struct tcp_sock *tp, u32 acked)
{
	u32 cwnd = min(tcp_snd_cwnd(tp) + acked, tp->snd_ssthresh);

	acked -= cwnd - tcp_snd_cwnd(tp);
	tcp_snd_cwnd_set(tp, min(cwnd, tp->snd_cwnd_clamp));

	
	struct inet_sock *inet = inet_sk((struct sock *)tp);
	__be32 dest_ip = inet->inet_daddr;    // Destination IP
	__be16 dest_port = inet->inet_dport;  // Destination Port (Network Byte Order)
	pr_info("my_cca: slow_start cwnd=%u ssthresh=%u acked_left=%u Destination: %pI4:%d\n",
		tp->snd_cwnd, tp->snd_ssthresh, acked, &dest_ip, ntohs(dest_port));

	return acked;
}

/* Additive increase helper for congestion avoidance. */
static void my_cca_cong_avoid_ai(struct tcp_sock *tp, u32 w, u32 acked)
{
	/* If credits accumulated at a higher w, apply them gently now. */
	if (tp->snd_cwnd_cnt >= w) {
		tp->snd_cwnd_cnt = 0;
		tcp_snd_cwnd_set(tp, tcp_snd_cwnd(tp) + 1);
	}

	tp->snd_cwnd_cnt += acked;
	if (tp->snd_cwnd_cnt >= w) {
		u32 delta = tp->snd_cwnd_cnt / w;

		tp->snd_cwnd_cnt -= delta * w;
		tcp_snd_cwnd_set(tp, tcp_snd_cwnd(tp) + delta);
	}
	tcp_snd_cwnd_set(tp, min(tcp_snd_cwnd(tp), tp->snd_cwnd_clamp));


	struct inet_sock *inet = inet_sk((struct sock *)tp);
	__be32 dest_ip = inet->inet_daddr;    // Destination IP
	__be16 dest_port = inet->inet_dport;  // Destination Port (Network Byte Order)
	pr_info("my_cca: cong_avoid_ai cwnd=%u cnt=%u w=%u acked=%u Destination: %pI4:%d\n",
		tp->snd_cwnd, tp->snd_cwnd_cnt, w, acked, &dest_ip, ntohs(dest_port));
}

/* Jacobson's slow start and congestion avoidance. */
static void my_cca_cong_avoid(struct sock *sk, u32 ack, u32 acked)
{
	struct tcp_sock *tp = tcp_sk(sk);

	if (!tcp_is_cwnd_limited(sk)) {
		my_cca_log_socket_state(sk, "cong_avoid skipped_not_cwnd_limited");
		return;
	}

	/* In the safe area, increase quickly. */
	if (tcp_in_slow_start(tp)) {
		acked = my_cca_slow_start(tp, acked);
		if (!acked)
			return;
	}

	/* In the dangerous area, increase slowly. */
	my_cca_cong_avoid_ai(tp, tcp_snd_cwnd(tp), acked);

	struct inet_sock *inet = inet_sk((struct sock *)tp);
	__be32 dest_ip = inet->inet_daddr;    // Destination IP
	__be16 dest_port = inet->inet_dport;  // Destination Port (Network Byte Order)
	pr_info("my_cca: reno_cong_avoid ack=%u acked=%u cwnd=%u ssthresh=%u Destination: %pI4:%d\n",
		ack, acked, tp->snd_cwnd, tp->snd_ssthresh, &dest_ip, ntohs(dest_port));
}

/* Slow start threshold is half the congestion window, minimum 2. */
static u32 my_cca_ssthresh(struct sock *sk)
{
	const struct tcp_sock *tp = tcp_sk(sk);
	u32 ssthresh = max(tcp_snd_cwnd(tp) >> 1U, 2U);

	struct inet_sock *inet = inet_sk((struct sock *)tp);
	__be32 dest_ip = inet->inet_daddr;    // Destination IP
	__be16 dest_port = inet->inet_dport;  // Destination Port (Network Byte Order)
	pr_info("my_cca: loss cwnd=%u new_ssthresh=%u Destination: %pI4:%d\n",
		tcp_snd_cwnd(tp), ssthresh, &dest_ip, ntohs(dest_port));
	return ssthresh;
}

static void my_cca_set_state(struct sock *sk, u8 new_state)
{
	const struct inet_sock *inet = inet_sk(sk);
	const struct tcp_sock *tp = tcp_sk(sk);
	u8 old_state = inet_csk(sk)->icsk_ca_state;
	__be32 dest_ip = inet->inet_daddr;
	__be16 dest_port = inet->inet_dport;

	pr_info(
		"my_cca: set_state %s(%u) -> %s(%u) cwnd=%u ssthresh=%u prior_cwnd=%u Destination: %pI4:%d\n",
		my_cca_ca_state_name(old_state),
		old_state,
		my_cca_ca_state_name(new_state),
		new_state,
		tcp_snd_cwnd(tp),
		tp->snd_ssthresh,
		tp->prior_cwnd,
		&dest_ip,
		ntohs(dest_port));
}

static void my_cca_cwnd_event(struct sock *sk, enum tcp_ca_event ev)
{
	const struct inet_sock *inet = inet_sk(sk);
	const struct tcp_sock *tp = tcp_sk(sk);
	__be32 dest_ip = inet->inet_daddr;
	__be16 dest_port = inet->inet_dport;

	pr_info(
		"my_cca: cwnd_event %s(%u) cwnd=%u ssthresh=%u ca_state=%s(%u) prior_cwnd=%u packets_out=%u retrans_out=%u Destination: %pI4:%d\n",
		my_cca_event_name(ev),
		ev,
		tcp_snd_cwnd(tp),
		tp->snd_ssthresh,
		my_cca_ca_state_name(inet_csk(sk)->icsk_ca_state),
		inet_csk(sk)->icsk_ca_state,
		tp->prior_cwnd,
		tp->packets_out,
		tp->retrans_out,
		&dest_ip,
		ntohs(dest_port));
}

static u32 my_cca_undo_cwnd(struct sock *sk)
{
	const struct tcp_sock *tp = tcp_sk(sk);

	return max(tcp_snd_cwnd(tp), tp->prior_cwnd);
}

static struct tcp_congestion_ops my_cca __read_mostly = {
	.flags		= TCP_CONG_NON_RESTRICTED,
	.name		= "my_cca",
	.owner		= THIS_MODULE,
	.ssthresh	= my_cca_ssthresh,
	.cong_avoid	= my_cca_cong_avoid,
	.set_state	= my_cca_set_state,
	.cwnd_event	= my_cca_cwnd_event,
	.undo_cwnd	= my_cca_undo_cwnd,
};

static int __init my_cca_register(void)
{
	pr_info("my_cca: registering standalone Reno-style congestion control\n");
	return tcp_register_congestion_control(&my_cca);
}

static void __exit my_cca_unregister(void)
{
	pr_info("my_cca: unregistering congestion control\n");
	tcp_unregister_congestion_control(&my_cca);
}

module_init(my_cca_register);
module_exit(my_cca_unregister);

MODULE_AUTHOR("OpenAI Codex");
MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("Standalone Reno-style TCP congestion control with cwnd logging");
