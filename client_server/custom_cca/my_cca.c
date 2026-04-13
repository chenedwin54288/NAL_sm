// SPDX-License-Identifier: GPL-2.0-only
/*
 * Standalone Reno-style TCP congestion control with logging for cwnd and
 * the corresponding TCP congestion-control state.
 */

// https://www.yonch.com/tech/linux-tcp-congestion-control-internals

#define pr_fmt(fmt) "TCP: " fmt

#include <linux/module.h>
#include <net/tcp.h>


/* Map Linux TCP congestion-control states to readable strings for logging. */
static const char *my_cca_ca_state_name(u8 state)
{
	switch (state) {
	case TCP_CA_Open:
		return "open";
	case TCP_CA_Disorder:
		return "disorder";
	case TCP_CA_CWR:
		return "cwr";
	case TCP_CA_Recovery:
		return "fast_retransmit_recovery";
	case TCP_CA_Loss:
		return "loss";
	default:
		return "unknown";
	}
}

/*
 * Derive a higher-level phase label from the raw TCP CA state and whether
 * the flow is still below ssthresh.
 */
static const char *my_cca_phase_name(const struct sock *sk)
{
	const struct tcp_sock *tp = tcp_sk(sk);
	u8 ca_state = inet_csk(sk)->icsk_ca_state;

	if (ca_state == TCP_CA_Recovery)
		return "fast_retransmit";

	if (ca_state == TCP_CA_Loss || ca_state == TCP_CA_CWR)
		return "loss_recovery";

	if (tcp_in_slow_start(tp))
		return "slow_start";

	return "congestion_avoidance";
}

/* Emit one consistent log record for cwnd-related events. */
static void my_cca_log_cwnd(const struct sock *sk, const char *reason, u32 prev_cwnd)
{
	const struct tcp_sock *tp = tcp_sk(sk);
	const struct inet_sock *inet = inet_sk(sk);
	__be32 dest_ip = inet->inet_daddr;
	__be16 dest_port = inet->inet_dport;

	pr_info(
		"my_cca: %s cwnd=%u prev_cwnd=%u ssthresh=%u phase=%s ca_state=%s(%u) Destination: %pI4:%d\n",
		reason,
		tcp_snd_cwnd(tp),
		prev_cwnd,
		tp->snd_ssthresh,
		my_cca_phase_name(sk),
		my_cca_ca_state_name(inet_csk(sk)->icsk_ca_state),
		inet_csk(sk)->icsk_ca_state,
		&dest_ip,
		ntohs(dest_port));
}

/*
 * SLOWSTART => new ACK => SLOWSTART
 *                OR
 * SLOWSTART => new ACK => SLOWSTART => CONGESTION AVOIDANCE
 * 
 *Exponential growth while cwnd is below ssthresh. 
 * - Slow start exits when cwnd grows over ssthresh and
 *   returns the leftover acks to adjust cwnd in congestion avoidance mode.
*/
static u32 my_cca_slow_start(struct tcp_sock *tp, u32 acked)
{
	u32 prev_cwnd = tcp_snd_cwnd(tp);
	u32 cwnd = min(prev_cwnd + acked, tp->snd_ssthresh);
	struct sock *sk = (struct sock *)tp;

	acked -= cwnd - prev_cwnd;
	tcp_snd_cwnd_set(tp, min(cwnd, tp->snd_cwnd_clamp));

	// if (tcp_snd_cwnd(tp) != prev_cwnd)
	// 	my_cca_log_cwnd(sk, "slow_start", prev_cwnd);

	return acked;
}

/* CONGESTION AVOIDANCE => new ACK => CONGESTION AVOIDANCE
   - roughly every w ACKs, increase cwnd by 1
   - if more ACKs arrive at once, cwnd can grow more than 1 in a single call
*/
static void my_cca_cong_avoid_ai(struct tcp_sock *tp, u32 w, u32 acked)
{
	u32 prev_cwnd = tcp_snd_cwnd(tp);
	struct sock *sk = (struct sock *)tp;

	if (tp->snd_cwnd_cnt >= w) {
		tp->snd_cwnd_cnt = 0;
		tcp_snd_cwnd_set(tp, tcp_snd_cwnd(tp) + 1);
	}

	tp->snd_cwnd_cnt += acked;
	// - Handle the case where a burst of ACKs causes snd_cwnd_cnt to exceed w by more than 1, 
	//   allowing cwnd to grow by more than 1 in a single call.
	// - keep only the remainder with tp->snd_cwnd_cnt -= delta * w, 
	//   cwnd to grow by more than 1 in a single call.
	if (tp->snd_cwnd_cnt >= w) {
		u32 delta = tp->snd_cwnd_cnt / w;

		tp->snd_cwnd_cnt -= delta * w;
		tcp_snd_cwnd_set(tp, tcp_snd_cwnd(tp) + delta);
	}

	tcp_snd_cwnd_set(tp, min(tcp_snd_cwnd(tp), tp->snd_cwnd_clamp));

	// if (tcp_snd_cwnd(tp) != prev_cwnd)
	// 	my_cca_log_cwnd(sk, "congestion_avoidance", prev_cwnd);
}

/*
 * SLOWSTART => new ACK => SLOWSTART
 *                OR
 * SLOWSTART => new ACK => SLOWSTART => CONGESTION AVOIDANCE
 * 
 * Main ACK-driven congestion-control callback used by TCP.
 * It chooses between slow start and additive increase.
 */
static void my_cca_cong_avoid(struct sock *sk, u32 ack, u32 acked)
{
	struct tcp_sock *tp = tcp_sk(sk);

	if (!tcp_is_cwnd_limited(sk))
		return;

	// if sender is cwnd-limited, try to grow the congestion window
	if (tcp_in_slow_start(tp)) {
		acked = my_cca_slow_start(tp, acked);
		if (!acked)
			return;
	}

	// If we have remaining ACKs after slow start, or if we're already above ssthresh, 
	// use congestion avoidance.
	my_cca_cong_avoid_ai(tp, tcp_snd_cwnd(tp), acked);
	(void)ack;
}

/* Recompute ssthresh after a congestion event, matching Reno behavior. */
static u32 my_cca_ssthresh(struct sock *sk)
{
	const struct tcp_sock *tp = tcp_sk(sk);
	u32 prev_cwnd = tcp_snd_cwnd(tp);
	u32 ssthresh = max(prev_cwnd >> 1U, 2U);

	//my_cca_log_cwnd(sk, "ssthresh", prev_cwnd);
	return ssthresh;
}

/* Log transitions into recovery/loss/open states as TCP changes CA state. */
static void my_cca_set_state(struct sock *sk, u8 new_state)
{
	const struct tcp_sock *tp = tcp_sk(sk);
	const struct inet_sock *inet = inet_sk(sk);
	u8 old_state = inet_csk(sk)->icsk_ca_state;
	__be32 dest_ip = inet->inet_daddr;
	__be16 dest_port = inet->inet_dport;

	pr_info(
		"my_cca: set_state %s(%u)->%s(%u) cwnd=%u ssthresh=%u phase=%s ca_state=%s(%u) Destination: %pI4:%d\n",
		my_cca_ca_state_name(old_state),
		old_state,
		my_cca_ca_state_name(new_state),
		new_state,
		tcp_snd_cwnd(tp),
		tp->snd_ssthresh,
		my_cca_phase_name(sk),
		my_cca_ca_state_name(new_state),
		new_state,
		&dest_ip,
		ntohs(dest_port));
}

static u32 my_cca_undo_cwnd(struct sock *sk)
{
	const struct tcp_sock *tp = tcp_sk(sk);

	return max(tcp_snd_cwnd(tp), tp->prior_cwnd);
}


// Log cwnd and CA state when ACKs are received, to observe how they evolve over time.
static void my_cca_pkts_acked(struct sock *sk, const struct ack_sample *sample)
{
	struct tcp_sock *tp = tcp_sk(sk);
	static u32 last_logged_cwnd;
	static u32 count = 0;
	u32 cwnd = tcp_snd_cwnd(tp);

	if (sample->rtt_us < 0)
		return;
	else if (count++ % 10 != 0)
		return;
	else if (cwnd == last_logged_cwnd)
		return;
	

	last_logged_cwnd = cwnd;

	const struct inet_sock *inet = inet_sk(sk);
	__be32 dest_ip = inet->inet_daddr;
	__be16 dest_port = inet->inet_dport;
	
	// if (count++ % 10 == 0) { // Log every 10th change to reduce log volume
	pr_info("my_cca: cwnd=%u rtt=%d phase=%s Destination: %pI4:%d\n", cwnd, sample->rtt_us, my_cca_phase_name(sk), &dest_ip, ntohs(dest_port));
	// }
}


static struct tcp_congestion_ops my_cca __read_mostly = {
	.flags		= TCP_CONG_NON_RESTRICTED,
	.name		= "my_cca",
	.owner		= THIS_MODULE,
	.ssthresh	= my_cca_ssthresh,
	.cong_avoid	= my_cca_cong_avoid,
	.set_state	= my_cca_set_state,
	.undo_cwnd	= my_cca_undo_cwnd,
	.pkts_acked = my_cca_pkts_acked,
};

static int __init my_cca_register(void)
{
	pr_info("my_cca: registering congestion control\n");
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
MODULE_DESCRIPTION("Reno-style TCP congestion control with cwnd/state logging");
