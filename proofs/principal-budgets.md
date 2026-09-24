# Principal budgets for shared-signal dyadic quantization

This document contains mathematical arguments, not proof-assistant output.
The executable checks in this repository falsify implementations on finite
instances; they are not mechanized proofs of the quantified statements below.
All statements concern the model defined here, not measured analog hardware.

## 1. Model and exact error effects

For each capture g choose real v_g in a nonempty closed rational interval
[l_g,h_g], encoding error z_g in [z_g^-,z_g^+], and analog error a_g in
[a_g^-,a_g^+]. Put u_g=z_g+a_g, s_g=v_g+u_g, d_g=z_g^-+a_g^-, and
e_g=z_g^++a_g^+. All these original coordinates, and additional additive
error origins eta_j in closed rational intervals, range over their Cartesian
product. This is a statement about admissible valuations, not probabilistic
independence. Captures that share a latent constraint are not distinct free
coordinates in this model.

For integer p, define Delta_p=2^p and

    Q_p(s)=Delta_p floor(s/Delta_p+1/2),   r_p(s)=Q_p(s)-s.

These are unsaturated zero-offset nearest quantizers, with exact ties toward
positive infinity. All converters attached to g see the same frozen value s_g.
There are no cascaded quantizers. A program is a finite acyclic affine DAG over
rational constants, ideal reads, analog reads, quantizer reads, and additive
error origins. Scaling and addition are exact in both semantics. Ideal reads
return v_g in both semantics. An analog read returns (v_g,s_g), a quantizer
read returns (v_g,Q_p(s_g)), and an error read returns (0,eta_j), where the
pair denotes ideal and implemented semantics.

An effect is a finite signed rational coefficient map with keys U_g, R_{g,p},
and H_j. The typing rules assign effect zero to constants and ideal reads,
U_g to analog reads, U_g+R_{g,p} to quantizer reads, and H_j to error reads.
Addition adds maps, rational scaling scales maps, and node reuse reuses its
map. Equal keys are merged, including cancellation; different capture ids
are never silently merged.

**Theorem 1 (exact effect identity).** For every well-formed program, every
output e, and every admissible valuation,

    implemented(e)-ideal(e)
      = sum_g [c_g u_g + sum_p w_{g,p} r_p(s_g)] + sum_j b_j eta_j,

where (c,w,b) is the map inferred for e.

**Proof.** Induct over the topological order. Constants and ideal reads have
identical semantics. An analog read differs by u_g. A quantizer read differs
by Q_p(s_g)-v_g = r_p(s_g)+u_g. An error read differs by eta_j. For addition,
subtract the two ideal operands from the two implemented operands and apply
the induction hypotheses. For scaling, distributivity gives the scalar times
the inductive error identity, including negative and zero scalars. Reusing a
node reuses the same value in both semantics and the same formal error
origins; it does not create new uncertainty. These are all syntax forms. QED.

This is a signed effect identity, not a rule for prematurely discharging each
intermediate expression to a nonnegative scalar error radius. Its strength is
conditional on retaining the capture and converter origin keys.

## 2. The phase-bit identity

Consider distinct nonzero weighted converter steps. Let delta be half the
smallest step, let P be the largest step, and write each step as delta*2^h,
where h is a positive integer. Translate s by a multiple t of P and write
s=t+delta*n+r with integer n>=0 and 0<=r<delta. Let b_j(n) be bit j of n.

**Lemma 2 (exact bit signature).** The residual of the step delta*2^h is

    r_h(s)=delta [2^h b_{h-1}(n) - sum_{j<h} 2^j b_j(n)] - r.

**Proof.** Translation by t changes the quantized value and input by the same
multiple of the converter step and hence leaves the residual invariant. Divide
n=q*2^h+k with 0<=k<2^h. The quantizer selects q*delta*2^h when k<2^{h-1}
and (q+1)*delta*2^h otherwise: the fractional remainder r/delta is below one,
so it cannot cross another integer threshold. At k=2^{h-1},r=0 the second
case applies by the tie rule. Subtract delta*n+r. The upper-half indicator is
b_{h-1}(n), and k=sum_{j<h}2^j b_j(n). QED.

For F(s)=sum_h w_h r_h(s)+lambda*s+c, let absent weights be zero. Collecting
terms gives

    F(s)=c+lambda*t + sum_j C_j b_j(n) + rho*r,
    C_j=delta*2^j [lambda + 2*w_{j+1} - sum_{h>j} w_h],
    rho=lambda-sum_h w_h.

For j beyond every converter exponent, C_j=lambda*delta*2^j. This is why
higher integer-range bits remain relevant for a nonzero affine term.
Negative source values need no signed-bit convention: choose
 t=floor(a/P)*P for a source interval [a,b], making s-t nonnegative.

## 3. Full-period support and its compressed form

Let H=log_2(P/delta). On one period [0,P), n ranges over every H-bit word and
r ranges independently over [0,delta). Thus the *closed convex hull* of the
joint residual vector is the affine image of [0,1]^H times [0,delta]. The
reachable set itself is generally neither convex nor a Cartesian product of
individual converter residual intervals. Taking a convex hull is exact for
linear support queries but not for arbitrary nonlinear downstream operations.

**Theorem 3 (exact full-period budget).** Let Delta_1<...<Delta_m be dyadic
steps, let w_i be arbitrary real weights, and S_i=sum_{k=i}^m w_k,
S_{m+1}=0. Then the infimum and supremum of sum_i w_i r_i(s) over a full
period are -B and B, where

    B = Delta_1/4 |S_1|
        + sum_{i=1}^m Delta_i/4 |w_i-S_{i+1}|
        + sum_{i=1}^{m-1} (Delta_{i+1}/4-Delta_i/2) |S_{i+1}|.

For rational weights the value is rational. The formula uses O(m) rational
arithmetic operations after sorting, not constant bit complexity.

**Proof.** The bit identity maps the center (1/2,...,1/2,delta/2) to zero in
every residual coordinate: the coordinate center is
 delta*(2^{h-1}-(2^h-1)/2)-delta/2=0.
Consequently the support in any direction is half the sum of absolute bit
coefficients plus delta/2 times the absolute within-cell slope. The last term
is Delta_1*|S_1|/4. At bit j=h_i-1 the coefficient is
(Delta_i/2)*(w_i-S_{i+1}), giving the middle sum. In a gap h_i<=j<h_{i+1}-1,
no converter starts at j+1, so the coefficient is -delta*2^j*S_{i+1}.
Half the geometric sum over these gap bits equals
(Delta_{i+1}/4-Delta_i/2)*|S_{i+1}|. There are no other bits. Linear support
of a set equals that of its closed convex hull; the half-open residual
coordinate may make one supporting endpoint a limit rather than an attained
value, but does not change the infimum or supremum. QED.

Grouping the collinear gap generators provides a zonotope with at most 2m
generators, even when the finest and coarsest exponents are far apart. This
compressed hull statement does not imply that exact membership in the original
nonconvex phase trace is solved by the same convex representation.

## 4. Sharp loss of independent local error intervals

Now take m consecutive steps Delta_i=d*2^{i-1}, with d>0. Define the usual
separated half-step radius T(w)=sum_i Delta_i*|w_i|/2.

**Theorem 4 (sharp factor).** For every real weight vector,

    B(w) <= T(w) <= (m+1)/2 * B(w).

The factor is attained by nonnegative weights whose sum is one, so it is not
an artifact of negative fusion weights or duplicate quantizers.

**Proof.** The first inequality follows by bounding every residual separately.
For the second, set y_i=Delta_i*(w_i-S_{i+1})/4. The triangular map is
invertible and

    sum_i y_i = d*S_1/4,
    w_i = (4/Delta_i) [y_i + (1/2)sum_{j>i}y_j].

The first identity follows by collecting the coefficient of w_k: it is
(Delta_k-sum_{i<k}Delta_i)/4=d/4. For the inverse, the formula for i=m is
immediate. The recurrence S_i=(w_i-S_{i+1})+2*S_{i+1}, solved backward,
yields the displayed expression for w_i. As consecutive steps have zero gap
terms in Theorem 3,

    B = |sum_i y_i| + sum_i |y_i|,
    T = sum_i |2*y_i + sum_{j>i} y_j|.

Write P_y=sum max(y_i,0) and N_y=sum max(-y_i,0). Then B=2max(P_y,N_y).
The unit ball B<=1 is the difference of two simplices
 {a:a>=0,sum a<=1/2} - {b:b>=0,sum b<=1/2}.
Indeed any such difference has positive and negative masses at most 1/2,
and any y with those masses uses a=y_+,b=y_-. Therefore the unit ball is the
convex hull of 0, the vectors +/-e_i/2, and (e_i-e_j)/2 for i!=j.

T is convex. On +/-e_i/2 its value is (i+1)/2. On (e_i-e_j)/2, i<j, it is
1+(j-i)/2: indices before i cancel, indices i and between i and j contribute
1/2 each, and index j contributes 1. These values are at most (m+1)/2.
A convex function on the convex hull of finitely many points is bounded by
its largest value at those points. Positive homogeneity proves the inequality
for B>0. If B=0 then y=0, hence w=0 and T=0.

For sharpness take w_i=2^{-i} for i<m and w_m=2^{1-m}. The weights sum to
one, only y_m is nonzero, and y_m=d/4. Thus B=d/2 and
T=(m+1)d/4. This attains the claimed factor, including m=1. QED.

**Corollary 4.1 (scope of the information loss).** An abstraction that retains
only separate half-step residual sets and must be sound for their Cartesian
completion cannot guarantee an m-independent approximation factor relative to
B. The product completion permits the simultaneous signs attaining T, while
Theorem 4 supplies true shared-input banks with T/B=(m+1)/2. This is not an
impossibility result for every type system, interval refinement, relational
analysis, or solver; it applies to the explicitly separated interface.

**Corollary 4.2 (all minimax normalized fusers).** If sum_i w_i=1, even allowing
signed weights, the minimum possible B is d/2. Equality holds exactly when
w_i>=S_{i+1} for all i. Equivalently, y_i>=0 and sum_i y_i=d/4. The optimal
weights form the affine image of a simplex whose j-th vertex has weights
2^{-i} for i<j, 2^{1-j} at i=j, and zero at i>j.

**Proof.** With the normalization, sum y_i=d/4. Theorem 4's identity gives
B=d/4+sum|y_i|>=d/2, with equality precisely when every y_i is nonnegative.
The inverse map sends the simplex vertices (d/4)e_j to the stated weights.
This also shows every minimax fuser is nonnegative. Independently, for
0<s<d/2 all converters return zero, so any normalized fuser has error -s
approaching -d/2; no normalized weights can improve the lower bound. QED.

The minimum is a worst-case statement. It is not a recommendation to build a
redundant converter bank: the finest converter alone also reaches d/2.

## 5. Bounded phase intervals and endpoint attainment

For F(s) from Section 2 on a closed rational interval [a,b], put
 t=floor(a/P)*P, n_a=floor((a-t)/delta), n_b=floor((b-t)/delta).
If n_a=n_b, the problem is a single affine segment with both endpoints closed.
Otherwise partition the input into its first partial half-open cell, the full
cells n_a+1,...,n_b-1, and the last partial closed cell. A singleton last
cell at a threshold must not be discarded.

**Lemma 5 (aligned cover).** A nonnegative integer interval with indices of
at most K bits has a disjoint cover by at most 2K aligned dyadic blocks. Each
block has the form {N,...,N+2^k-1}, where 2^k divides N, and its members
have fixed high bits and independently free low k bits.

**Proof.** View the interval in the complete binary tree of the K-bit integer
universe. The maximal dyadic subintervals contained in the target interval
partition it: any point can ascend until its parent leaves the interval.
At each depth only the two boundary paths can have a fully included sibling
not already covered by a larger included ancestor. There are at most two
blocks per depth, hence at most 2K. Alignment means the low k bits of N are
zero; adding any integer below 2^k varies exactly those bits without a carry
into the prefix. A greedy left-to-right maximal aligned block cover produces
these maximal blocks. QED.

**Theorem 6 (exact bounded support).** On a full block the optimum bit word
sets each free bit to one exactly when its coefficient has the favorable
sign. The residual term chooses r=0 or the limit r=delta according to the
sign of rho. On either partial cell it chooses the corresponding affine
endpoint. Taking the smallest/largest candidate over the cover gives the
exact infimum/supremum and a correct flag for whether it is attained.

**Proof.** Lemma 2 makes the objective separable in every free bit and r.
Every allowed bit combination and every r in [0,delta) corresponds to an
actual input in a full block. Thus coordinatewise sign choices yield exact
support. A partial cell has a single fixed n and is affine in r, so its
endpoint support is exact. A right endpoint r=delta is outside that cell;
it is a one-sided limit unless the same value is achieved elsewhere. The
finite union's support is the extremum among piece supports. It is attained
iff some piece with that extremal value attains it. For zero rho choose the
included left endpoint, not a fictitious unattained right endpoint. At a
threshold the next cell evaluates the actual tie convention separately from
the preceding cell's limit. The partition includes every admissible s and
no interior point outside [a,b]. QED.

An interval may span many periods. The high bits introduced by lambda*s
remain in the representation, so the proof also handles that case. If all
weights cancel, use delta=P=1; the calculation reduces to ordinary affine
interval support.

## 6. Encoding and analog envelopes without losing causality

**Lemma 7 (exact fiber).** If v in [l,h], u in [d,e], and s=v+u, the possible
s values form [l+d,h+e], and for each s in this interval,

    max(d,s-h) <= u <= min(e,s-l).

**Proof.** Substitute v=s-u into l<=v<=h and intersect its consequences
s-h<=u<=s-l with d<=u<=e. The intersection is nonempty throughout the
Minkowski sum interval and gives exactly the possible pairs. QED.

For c*u+f(s), maximizing over u at fixed s chooses the upper fiber for c>=0
and the lower fiber for c<0. Minimization reverses the choice. The upper
fiber is s-l up to s=l+e and e afterward. The lower fiber is d up to s=h+d
and s-h afterward. Therefore each extremum reduces to two closed affine
pieces in s, and Theorem 6 applies with lambda equal to c times the chosen
fiber slope. The pieces agree on u at their shared pivot, so duplicated
pivot evaluations do not change support or attainment.

**Theorem 8 (exact capture support).** This fiber reduction computes the
infimum and supremum of c*u+sum_p w_p*r_p(v+u), with correct attainment,
over the original encoding/analog/ideal boxes.

**Proof.** Lemma 7 justifies exact elimination of v. The objective is affine
in u for fixed s, making the appropriate fiber endpoint exact. Theorem 6 is
exact on each resulting s-piece. Finally every u in [d,e] has an admissible
split into encoding and analog errors: choose z=max(z^-,u-a^+), a=u-z.
Then z>=z^-, a<=a^+; from u>=z^-+a^- and u<=z^++a^+ one obtains
z<=z^+ and a>=a^-. Thus no support point or interior approximation uses an
unrealizable pre-quantization error. QED.

**Corollary 8.1 (wide input range).** If h-l>=P, then the capture support is
[min(c*d,c*e)-B, max(c*d,c*e)+B], with B from Theorem 3. For any fixed u,
[v+u:v in [l,h]] covers a complete residual period. Hence each endpoint of
c*u can coexist with arbitrarily close approximations to either residual
support endpoint. The converse bounds follow from the separate extrema.
This corollary gives support values only; its attainment requires the
interval-aware calculation when exact ties matter.

## 7. Principal budgets and strict rational witnesses

Sum the capture infima and the signed minima of the independent eta intervals
to obtain L. Sum their suprema and signed maxima to obtain U.

**Theorem 9 (principal scalar and maximum-norm budgets).** The least
nonnegative bound on the absolute output error is B_e=max(0,-L,U). For a
finite output vector with the maximum norm it is max_e B_e.

**Proof.** Theorem 1 is an exact identity. Each summand is bounded by its
support, so [L,U] encloses the output error. Conversely, every group's
support can be approached arbitrarily closely, and the Cartesian domain
allows these approximations to be chosen together; a finite sum preserves
arbitrarily close approximation. Thus L and U are the true infimum and
supremum. Their absolute maximum is the least nonnegative uniform bound.
For finitely many rows, sup_valuation max_e |E_e| = max_e sup_valuation
|E_e|. The <= direction follows rowwise; the >= direction follows by choosing
any row arbitrarily close to its own support. The different rows need not
attain their extrema simultaneously. QED.

**Corollary 9.1 (best correct interval discharge).** Let S_e be the set of
all concrete output errors over the admitted valuations. The analyzer returns
[L,U]=[inf S_e,sup S_e], the least closed real interval containing S_e. Hence no
sound closed-interval analysis of the same concrete semantics can return a proper
subinterval. Mapping [L,U] to max(0,-L,U) gives the least centered absolute-error
radius.

**Proof.** The proof of Theorem 9 establishes that L and U are the true infimum
and supremum of S_e. Every closed interval containing S_e must contain both, and
therefore must contain [L,U]. The centered interval [-beta,beta] contains [L,U]
exactly when beta>=max(0,-L,U). QED.

This is a best-correct-abstraction statement for the declared semantics and the
closed-interval target. It does not claim that intervals are complete for nonlinear
clients, that the origin map is the only possible principal type language, or that
an intermediate scalar radius can replace the signed effect without losing later
cancellation.

**Worked three-rate discharge.** Let v range over [0,1], take zero encoding and
analog envelopes, and average quantizers with steps 1/4, 1/2, and 1. The exact
error is

    E(v)=(r_{-2}(v)+r_{-1}(v)+r_0(v))/3.

The source interval covers the largest period. With Delta=(1/4,1/2,1),
w=(1/3,1/3,1/3), and suffix sums S=(1,2/3,1/3), Theorem 3 gives

    B=1/16+1/48+0+1/12=1/6.

The separated half-step radius is 7/24. At v=1/2 the two finer quantizers return
1/2 and the unit-step quantizer returns 1, so the average is 2/3 and E=1/6.
Thus v=1/2 is an attained rational witness against any declaration below 1/6,
including 1/10. The supplied example certificate records the effect, phase support,
attainment, and direct paired-semantics replay.

**Theorem 10 (rational strict violation).** For rational program constants,
interval endpoints, and beta satisfying 0<=beta<B_e, a rational admissible
valuation with |implemented(e)-ideal(e)|>beta can be constructed.

**Proof.** Select a support side of magnitude B_e and let margin=B_e-beta.
For N nonzero capture groups, choose the recorded endpoint for every group
whose relevant support is attained. If an endpoint is unattained, it is a
right-cell limit with nonzero affine slope rho and positive remaining cell
width w. Replace r=delta by r=delta-epsilon, where
 epsilon=min(w/2, margin/(4*max(1,N)*|rho|)).
This stays in the same partial cell or full block and loses at most
margin/(4*max(1,N)) toward the chosen support. The sum of losses is at most
margin/4. Evaluate u on the same chosen fiber piece, put v=s-u, and use the
admissible encoding/analog split from Theorem 8. Every coordinate is rational.
Choose independent eta endpoints according to their signed contribution.
Inactive groups can use arbitrary rational endpoints. The resulting error
has the selected sign and magnitude at least B_e-margin/4>beta. The case
N=0 uses only attained interval endpoints. A maximum-norm witness chooses
a row attaining the maximum among the finite row budgets. QED.

This is not a sparsest witness, a minimum-distance violation, or a smallest
program counterexample. Principality over real declared budgets follows as
well: for any real beta<B choose a rational intermediate threshold in
(max(0,beta),B), unless B=0 where no nonnegative smaller budget exists.

## 8. Algorithmic and trust boundaries

The implemented interval algorithm uses O(K) cover pieces and O(K^2+m*K)
rational operations in its straightforward independent replay; the analyzer
uses suffix sums and O(K^2+m) rational operations after sorting. K includes
the expanded precision span and bits needed for the translated interval's
largest fine-cell index. Rational arithmetic has nonconstant cost. A binary
encoding of an exponent does not make expansion to 2^p polynomial in its
encoded exponent length. No unqualified strongly polynomial claim is made.

The certificate contains coefficients, a complete aligned cover, both supports,
endpoint-attainment flags, and actual or limiting coordinates. The replay
implementation independently validates the entire input DAG, rederives output
effects by reverse accumulation, recomputes coefficients by summing individual
converter signatures, checks the contiguous cover, verifies each piece's
support and attainment, and directly evaluates strict witnesses in a separate
interpreter. Its checks instantiate the preceding lemmas. The Python checker
itself has not been proved correct in a proof assistant, and arithmetic,
interpreter, and file parsing remain trusted. Mutation rejection is finite
validation, not comprehensive security assurance.

**Theorem 11 (certificate adequacy under exact replay).** Suppose an admitted
program certificate is checked in exact rational arithmetic by (i) validating the
entire DAG and rederiving its signed effect, (ii) checking that every aligned cover
is contiguous, nonoverlapping, and exactly covers its declared phase interval,
(iii) checking every piece support, fiber choice, and endpoint-attainment flag
against Sections 2, 5, and 6, and (iv) adding group intervals under the original
Cartesian capture and auxiliary-origin contract. Then the accepted output interval
is the best correct closed-interval abstraction. If a recorded valuation is also
admissible under the input envelopes and the direct paired interpreter evaluates a
strict error above the challenged budget, that valuation is a concrete
counterexample to the declaration.

**Proof.** Effect rederivation instantiates Theorem 1. Cover, coefficient, and
piece checks instantiate Lemma 2 and Theorem 6; fiber checks instantiate Lemma 7
and Theorem 8. Exact group supports therefore sum to [L,U] in Theorem 9, and
Corollary 9.1 makes this interval least among all sound closed intervals. For the
second statement, the direct interpreter evaluates the exact ideal and implemented
semantics at coordinates already checked against the envelopes, so its strict
rational inequality is a direct semantic violation. QED.

The theorem is conditional on a correct exact-arithmetic replay implementation; it
is not a mechanized correctness proof of the Python program. Replay rejection is
diagnostic rather than a mathematical refutation, because malformed serialization,
an incomplete cover, or an implementation defect can reject a valid mathematical
budget.

The admitted model excludes saturation, stochastic guarantees, signal-dependent
or cross-capture hidden constraints, cascades, converter offsets, nonlinear
downstream arithmetic, implicit digital roundoff, and all hardware cost or
energy conclusions. Q_{p=0}(-1/2)=0 differs from -Q_{p=0}(1/2)=-1, so negative-gain
rewrites cannot silently change the tie convention. For steps 1 and 2,
Q_{p=1}(Q_{p=0}(3/5))=2 but Q_{p=1}(3/5)=0, so a cascade is not a parallel converter.
Refining one arm of a cancelling difference can increase its joint error;
individual-precision monotonicity is not a law of this language.

## 9. Relation to published converter fusion

McMichael, Maymon, and Oppenheim, “Exploiting Cross-Channel Quantizer Error
Correlation in Time-Interleaved Analog-to-Digital Converters,” ASILOMAR 2011,
pp. 525–529, Section IV and Table II, already establish a deterministic
relation between different-precision residuals and derive covariance-aware
weighted least-squares fusion. Consequently neither correlated quantization
nor using correlated errors in positive-weight fusion is claimed here as a
new phenomenon. Their statistical criterion is not the universal support
criterion of Theorems 3–10.

For comparison, under the *additional hypothetical assumption* of a uniformly
distributed phase over one period and consecutive steps, the same bit identity
makes bits independent Bernoulli(1/2) and r uniform on [0,d/2). For normalized
weights, centered error has variance sum_i y_i^2+d^2/48. Since sum_i y_i=d/4,
this is minimized at y_i=d/(4m), giving d^2(m+3)/(48m). This derivation is a
consistency calculation with the published statistical fusion, not a new
empirical noise model. These weights lie in the minimax simplex of Corollary
4.2. Their separated radius is d(m+3)/8 although their worst-case budget stays
d/2. The artifact reads all five rational weight rows from the source's Table
II and checks this statement directly. It does not reproduce their sampling
simulations or claim their physical performance.
