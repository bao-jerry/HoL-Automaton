# The HoL Automaton:
In the book *House of Leaves* by Mark Z. Danielewski, a central mystery was that the house of Will Navidson and Karen Green was measured to be 5/16 inches wider on the inside—a geometrical impossibility. At first, they assumed this was a dismissable measurement error, but after extensive re-measurements, the anomaly persisted.

The HoL (House of Leaves) Automaton is a deterministic cellular automaton I implemented that displays several curious emergent behaviors, including an anomaly that reminded me of this book. Let's first go through the automaton's simple rules.

## HoL Automaton rules:
1) Start with a black-and-white grid of cells, which is to be overwritten on each round with a new color configuration.
2) Each cell is either of rule type "3" or rule type "4", with the rule type for each cell being fixed throughout the automaton's duration. The rule types are distributed in a strict checkerboard pattern in the grid.
3) On each round, each cell is either colored white (0) or black (1).
4) On each round, the coloring rule for a cell is as follows:
   1) If the cell has rule type 3, then it becomes black if its # of black neighbors (including diagonal ones) from the previous round is 1 mod 3. It becomes white otherwise.
   2) If the cell has rule type 4, then it becomes black if its # of black neighbors (including diagonal ones) from the previous round is 1 mod 4. It becomes white otherwise.

Extra notes:
- The edges of the grid wrap around to the opposite edge.
- The length and width of the grid are even so the checkerboard pattern joins correctly at the wrapped edges.

## Emergent behaviors:
### Self-healing stability:
Starting from almost any random initial distribution of black cells (e.g. 1% black cells, 50% black cells, 99% black cells, etc.), the grid will eventually converge to ~30.0% black cells. Moreover, the 30.0% convergence was observed to hold across different grid dimensions and random seeds.

Note that for finite grids, the automaton will eventually cycle, so grids of different dimensions will obviously have tiny differences in their measured convergence limits due to finite sequence length. On the other hand, based on my experimentation, my core conjecture is that as the length and width of the grids approach infinity, their limits approach a universal convergence value near 30.0%.

### The anomaly:
The 30.0% number cannot be accounted for by simulating the automaton with a standard probabilistic model, which instead predicts a proportion of 29.3%—a consistent percentage point anomaly of +0.7 pp that is unexplained by one-off measurement error (30.0% holds consistently across different random seeds and grid dimensions). See below for the 29.3% figure derivation.

Since HoL is a deterministic automaton rather than a random process, one might be tempted to explain away this discrepancy by citing the fact that a probabilistic model is a non-exact approximation of a deterministic process and leave it at that. However, the uncomfortable questions that remain is "if that didn't work, then how *do* we actually derive the ~30.0% convergence limit?", and—"can it be derived from first principles without needing to assume an a posteriori fact?"

## Probabilistic Modeling:
Here, I'll derive the 29.3% figure via an idealized probabilistic model of the HoL automaton. We make the following assumptions:
1) Eventually, the proportion of black cells stabilizes
2) Each rule type 3 cell simulates an independent Bernoulli random variable with probability $p_3$ of being black on any given round.
3) Each rule type 4 cell simulates an independent Bernoulli random variable with probability $p_4$ of being black on any given round.

Because the rule types form a checkerboard, every cell has four type 3 neighbors and four type 4 neighbors. Suppose exactly $a$ of the four type 3 neighbors are black and exactly $b$ of the four type 4 neighbors are black. Under the independence assumption, the probability of this is

$$
Q(a,b)=
\binom{4}{a}p_3^a(1-p_3)^{4-a}
\binom{4}{b}p_4^b(1-p_4)^{4-b}.
$$

The cell has $a+b$ black neighbors. Therefore, if $P_k$ is the probability that a cell has exactly $k$ black neighbors, then

$$
P_k=
\sum_{a=\max(0,k-4)}^{\min(4,k)} Q(a,k-a).
$$

Here, $b=k-a$, and the limits ensure that both $a$ and $b$ remain between 0 and 4.

A type 3 cell becomes black when it has 1, 4, or 7 black neighbors, so its probability of being black on the next round is

$$
P_1+P_4+P_7.
$$

A type 4 cell becomes black when it has 1 or 5 black neighbors, so its probability of being black on the next round is

$$
P_1+P_5.
$$

Since we assumed that the black proportions eventually stabilize, the probabilities before and after a round must be equal. Thus, $p_3$ and $p_4$ must satisfy

$$
p_3=P_1+P_4+P_7,
$$

$$
p_4=P_1+P_5.
$$

Starting from $p_3=p_4=0.5$ and repeatedly replacing each value with the corresponding right-hand side gives

$$
p_3\approx0.3363155,
\qquad
p_4\approx0.2489347.
$$

Exactly half the cells are type 3 and half are type 4. The model's predicted overall proportion of black cells is therefore

$$
\frac{p_3+p_4}{2}
=\frac{0.3363155+0.2489347}{2}
\approx0.292625,
$$

or approximately **29.3%**.

## Open Questions:
- A first-principles derivation of the ~30.0% stabilizing limit that does not smuggle in a posteriori assumptions. In particular, overfitting a model to the experimental observations without justifying the modelling assumptions from first principles is invalid.
- A first-principles proof for the black tile proportion stabilizing at all.
