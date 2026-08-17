## Emergent Homeostat (EH) Automaton rules:
1) Start with a black-and-white grid of cells, which is to be overwritten on each round with a new color configuration.
2) Each cell is either of rule type "3" or rule type "4", with the rule type for each cell being fixed throughout the automaton's duration. The rule types are distributed in a strict checkerboard pattern in the grid.
3) On each round, each cell is either colored white (0) or black (1).
4) On each round, the coloring rule for a cell is as follows:
   1) If the cell has rule type 3, then it becomes black if its # of black neighbors (including diagonal ones) from the previous round is 1 mod 3. It becomes white otherwise.
   2) If the cell has rule type 4, then it becomes black if its # of black neighbors (including diagonal ones) from the previous round is 1 mod 4. It becomes white otherwise.

Extra notes:
- The edges of the grid wrap around to the opposite edge.
- The length and width of the grid are even so the checkerboard pattern joins correctly at the wrapped edges.

## Emergent behavior: self-recovering stability:
The EH automaton displays a remarkable ability to recover stability from nearly any extreme initial state. Starting from nearly any random initial distribution of black cells (e.g. 1% black cells, 50% black cells, 99% black cells, etc.), the grid will eventually converge to ~30.0% black cells. This 30.0% convergence phenomenon was observed to hold across various grid dimensions, initial black cell proportions, and random seedings.

What makes this 30.0% figure particularly interesting is that it's not precisely derivable from standard probabilistic modeling of the automaton. Indeed, if one were to simulate the automaton with a standard probabilistic model, one would arrive at a predicted black proportion of 29.3%, which is an imperfect approximation with a ~0.7 percentage point error. This is a small error, but a real one that persists across all kinds of initializations. It is therefore reasonable to ask: "Given that the automaton's rules are fully deterministic, shouldn't we deem it likely that there exists an explicit, first-principles derivation of the eventual proportion of black tiles?"

We have the following mathematical open questions:

## Mathematical Open Questions:
- Why should the EH automaton's black cell proportion stabilize at all?
- How can the ~30.0% convergence value for black cell proportion be derived from first principles?

## Probabilistic Modeling:
Here, I'll derive the 29.3% figure mentioned earlier via an idealized probabilistic model of the EH automaton. We make the following assumptions:
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
