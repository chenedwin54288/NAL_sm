**MOTIVATION:**

* ISP uses limiter to control the streaming rate, 
policing => drop pkts when the queue is full
shaping => control the queue\_size
* when limiter is applied, we are not able to use the full band available
because of how the cca works 
* Franziska's work 
=> explored on ns3 to see if we know the parameters, how much improvement we could observe
=> we know that under the scenario when "queue size is small", we are able to achieve a 33%
     throughput gain 
* Martyna's work

However, both works were done in a simulated environment, in this project, we want to test it
in a real-life scenario.  We thus built a setup where we have two computers connecting through one router.

We then added a TBF on the forward path to limit the data.





**SETUP:**

*Extracting the cwnd*: initially with "ss" command

&#x20;                                   => did not work, cause samping speed cannot keep up

&#x20;                                  ... solution was to "change the kernel code directly" 

&#x20;                                        How did we change the kernel code?

*Extracting using  pr\_info()*: was able to extract but does not always start from 10

&#x20;                                                => because we were overwriting the kernel ring

&#x20;                                               ... solution set sampling frequency (every 100ACKs or when phase changes)

&#x20;                                               ... make a subprocess that cleans the ring buffer



*Adding TBF*: with the setup above, we still observe plateau (do we?)

&#x20;                   => Why? ... solution was to add a TBF



*Finalizing the setup*:

\- sever <-TBF-> router <--> client

\- run script where user specifies all the parameters

\- step by step workflow (example)

... at the end, also added an automation script that does this for us



*Parameters Tested in the setup*:

QUEUE\_SIZES=(5840, 11680, 23360, 46720, 93440)

TOKEN\_GENERATION\_RATES=(500 750 1000)

BURST\_SIZES=(5840 12500 25000 50000 100000)





**WINDOW COMPARISON:**

* **We compared the windows between TCP Reno, Empirical, "BDP + queue size - 1MSS (algo2)" and "BDP + 1MSS (algo2)"**
* **How did we determine the empirical cwnd?** 
... taking max average cwnd of the TCP Reno, using this to gradually lower down the cwnd until loss rate == 0 

&#x20;        What is loss rate => smallest "#loss / #total logged phase" 

=> improvement of the throughput under the assumption that we know the token bucket parameter

&#x20;   (token generation rate, queue size and burst size)

=>show that when the queue\_size is small, this is where we are able to observe 

&#x20; most performance increase (heap map with performance gain in percentage)

&#x20;   ... which matches with Franziska's testing result    

=> Show the case when: TGR == 1Gib, queue==4p, burst\_size==50000

&#x20;   - TCP Reno

&#x20;   - Empirical Rate 

&#x20;  ... here people might ask why does the cwnd drop from cwnd: 10 to cwnd: < 10 (apparently this will still be in

&#x20;        slow\_start phase???). Be sure to know how to answer this question



However...

=> Now show the diagram where algorithm1 and algoritm2 does not really apply to our case

&#x20;    ... empirical cwnd, and tcp cwnd is usually smaller than algo2 and algo1

&#x20;         coz the server does bulk send and the R\_arrival rate is inconsistent

If we reverse calculate the R\_arrival rate, then we are able to get a cwnd hat is close to 

the empirical value

... people might ask, why don't you send in a rate so that R\_arrival stays the same, or is a bit bigger 

than the token generation rate





Ok now, we want to test whether we are able to achieve the same result from the receiver side

Because normally, the TBF is on the receiver side (ingress queue), thus receiver should be the one

sending RWND to the server to cap the sending rate





**ESTIMATING THE TOKEN GENERATION RATE**:

Our previous experiments were based on the fact that we know all the TBF parameters

But receiver is the one that should send the rwnd cap to the sender, so it would be better

for the receiver to estimate the parameters



=> we tried Martynas's way: culmulative bytes arrival approach

How did we do this?

... when the burst size is not big, we are able to determine a server side 

BDP quite accurately (so same results as the simulation done in ns3





**LIMITATION \&\& Future Work:**

* rtt is 0.4ms which is very small
* Integrate with WeHeYL WeHeY to detect the bottleneck, once we know that the end  point
ISP is the bottleneck, we can then use the way above to maximize the queue\_space
* If R\_arrival rate is indeed the reason why the algorithm1 does not work,
we need to find a way to estimate this (which is hard because under small queues, the cwnd is smaller than the BDP)







