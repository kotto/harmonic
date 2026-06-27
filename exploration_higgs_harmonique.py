import math

phi = (1 + math.sqrt(5)) / 2
pi = math.pi
e = math.e
sqrt2 = math.sqrt(2)
sqrt3 = math.sqrt(3)
sqrt5 = math.sqrt(5)
e_pi = e / pi

H = [phi, pi, e, sqrt2, sqrt3, sqrt5, e_pi]
names = ['phi', 'pi', 'e', 'sqrt2', 'sqrt3', 'sqrt5', 'e/pi']

print("=" * 70)
print("EXPLORATION HARMONIQUE DE LA MASSE DU BOSON DE HIGGS")
print("=" * 70)

print("\nHn values:")
for i, (name, val) in enumerate(zip(names, H)):
    print(f"  H{i+1} = {name:6s} = {val:.10f}")

# Reference masses (GeV)
mH_exp = 125.20   # Higgs boson mass (PDG 2023)
v_vev   = 246.22  # Electroweak VEV
mW      = 80.377  # W boson
mZ      = 91.1876 # Z boson
mt      = 172.5   # Top quark (pole mass ~172.5 GeV)
me      = 0.511e-3
mp      = 0.938   # proton

print(f"\nReference masses (GeV):")
print(f"  Higgs m_H   = {mH_exp} GeV")
print(f"  VEV v       = {v_vev} GeV")
print(f"  W boson m_W = {mW} GeV")
print(f"  Z boson m_Z = {mZ} GeV")
print(f"  Top m_t     = {mt} GeV")

print(f"\nKey ratios with Higgs:")
print(f"  m_H / m_W     = {mH_exp / mW:.8f}")
print(f"  m_H / m_Z     = {mH_exp / mZ:.8f}")
print(f"  m_H / v       = {mH_exp / v_vev:.8f}")
print(f"  v / m_H       = {v_vev / mH_exp:.8f}")
print(f"  m_H / (m_W+m_Z)/2 = {mH_exp / ((mW+mZ)/2):.8f}")
print(f"  m_H / m_t     = {mH_exp / mt:.8f}")

print(f"\n  m_W + m_Z - m_H = {mW + mZ - mH_exp:.4f} GeV")
print(f"  sqrt(m_W*m_Z)   = {math.sqrt(mW*mZ):.4f} GeV")
print(f"  (m_W+m_Z)/2     = {(mW+mZ)/2:.4f} GeV")

# ============================================================
# SEARCH FOR HARMONIC EXPRESSIONS
# ============================================================
print("\n" + "=" * 70)
print("CANDIDATE HARMONIC EXPRESSIONS FOR m_H")
print("=" * 70)

candidates = []

# Strategy 1: m_H expressed as product of Hn powers
# We look for m_H / m_W or m_H / m_Z as harmonic products

# Let's test all possible combinations of small integer exponents
# for the first 6 Hn values
exponents = [-5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5]

print("\n--- Strategy 1: m_H/m_W as product of Hn powers ---")
best_mhw = []
target = mH_exp / mW  # ~1.5576
print(f"Target: m_H/m_W = {target:.8f}")

# Test some promising combinations manually
tests_mhw = [
    ("phi^1 * pi^0 * e^0 * sqrt2^0 * sqrt3^0 * sqrt5^0", phi**1),
    ("phi^1 * pi^0 * e^0 * sqrt2^-1 * sqrt3^0 * sqrt5^0", phi**1 * sqrt2**-1),
    ("phi^2 * pi^0 * e^0 * sqrt2^-1 * sqrt3^-1 * sqrt5^0", phi**2 * sqrt2**-1 * sqrt3**-1),
    ("phi^1 * pi^1 * e^0 * sqrt2^-1 * sqrt3^-1 * sqrt5^0", phi**1 * pi**1 * sqrt2**-1 * sqrt3**-1),
    ("phi^1 * pi^1 * e^-1 * sqrt2^0 * sqrt3^0 * sqrt5^0", phi**1 * pi**1 * e**-1),
    ("phi^0 * pi^1 * e^-1 * sqrt2^1 * sqrt3^1 * sqrt5^0", pi**1 * e**-1 * sqrt2**1 * sqrt3**1),
    ("phi^1 * e^-1 * pi^0 * sqrt2^1 * sqrt3^0 * sqrt5^0", phi * e**-1 * sqrt2),
    ("phi^0 * pi^1 * e^0 * sqrt2^0 * sqrt3^0 * sqrt5^0 / 2", pi / 2),
    ("pi * phi / e", pi * phi / e),
    ("pi * sqrt2 / phi", pi * sqrt2 / phi),
    ("pi * phi / (e * sqrt2)", pi * phi / (e * sqrt2)),
    ("pi^2 / (phi * e)", pi**2 / (phi * e)),
    ("(pi * phi)^0.5", (pi * phi)**0.5),
    ("phi * sqrt3 / sqrt5", phi * sqrt3 / sqrt5),
    ("phi^2 / sqrt3", phi**2 / sqrt3),
    ("e * phi / pi", e * phi / pi),
    ("(phi^3 / pi^2) * sqrt2", (phi**3 / pi**2) * sqrt2),
]

for name, val in tests_mhw:
    err = abs(val - target) / target * 100
    if err < 10:
        best_mhw.append((name, val, err))
        print(f"  {name:50s} = {val:.8f}  err={err:.3f}%")

print(f"\n--- Strategy 2: m_H/v as product of Hn powers ---")
target_v = mH_exp / v_vev  # ~0.5086
print(f"Target: m_H/v = {target_v:.8f}")

tests_mhv = [
    ("1/phi", 1/phi),
    ("1/sqrt(phi)", 1/math.sqrt(phi)),
    ("pi/(2*phi)", pi/(2*phi)),
    ("e/(phi*pi)", e/(phi*pi)),
    ("sqrt2/phi", sqrt2/phi),
    ("sqrt3/e", sqrt3/e),
    ("sqrt5/pi", sqrt5/pi),
    ("(e/pi)^2", (e/pi)**2),
    ("(e/pi) * phi", (e/pi) * phi),
    ("phi / (pi * sqrt2)", phi / (pi * sqrt2)),
    ("e * sqrt2 / (pi * phi)", e * sqrt2 / (pi * phi)),
    ("sqrt3 / (phi * sqrt2)", sqrt3 / (phi * sqrt2)),
    ("pi / (e * phi)", pi / (e * phi)),
    ("1 / sqrt3", 1/sqrt3),
    ("phi / e", phi / e),
    ("sqrt5 / (phi * sqrt3)", sqrt5 / (phi * sqrt3)),
    ("(e/pi) * sqrt2 / phi", (e/pi) * sqrt2 / phi),
]

for name, val in tests_mhv:
    err = abs(val - target_v) / target_v * 100
    if err < 15:
        print(f"  {name:50s} = {val:.8f}  err={err:.3f}%")

print(f"\n--- Strategy 3: m_H/m_Z as product of Hn powers ---")
target_z = mH_exp / mZ  # ~1.3730
print(f"Target: m_H/m_Z = {target_z:.8f}")

tests_mhz = [
    ("sqrt2", sqrt2),
    ("1 + 1/phi", 1 + 1/phi),
    ("phi - 1/phi", phi - 1/phi),
    ("phi/e * pi", phi/e*pi),
    ("e/2", e/2),
    ("(phi * e) / pi", (phi * e) / pi),
    ("sqrt3 * phi / pi", sqrt3 * phi / pi),
    ("pi * sqrt2 / (phi * e)", pi * sqrt2 / (phi * e)),
    ("phi^2 / (pi * sqrt3)", phi**2 / (pi * sqrt3)),
]

for name, val in tests_mhz:
    err = abs(val - target_z) / target_z * 100
    if err < 15:
        print(f"  {name:50s} = {val:.8f}  err={err:.3f}%")

# ============================================================
# Strategy 4: m_H from known harmonic ratios
# ============================================================
print(f"\n--- Strategy 4: Building m_H from known leptonic ratios ---")
ratio_mu_e = 206.7710
ratio_tau_mu = 16.8168
print(f"m_mu/m_e = {ratio_mu_e}")
print(f"m_tau/m_mu = {ratio_tau_mu}")

# Harmonic expressions for these ratios
r_mu_e_harm = phi**-3 * pi**3 * e**1 * sqrt2**2 * sqrt3**3
r_tau_mu_harm = phi**1 * pi**3 * e**2 * sqrt2**-1 * sqrt3**-5
print(f"m_mu/m_e (harm) = {r_mu_e_harm:.4f}")
print(f"m_tau/m_mu (harm) = {r_tau_mu_harm:.4f}")

# The Higgs could be related to tau mass
m_tau = 1.77686  # GeV
print(f"\nm_tau = {m_tau} GeV")
print(f"m_H / m_tau = {mH_exp / m_tau:.8f}")

# Test harmonic candidates for m_H/m_tau
target_ht = mH_exp / m_tau
tests_mht = [
    ("phi^2 * pi * e^-1 * sqrt3", phi**2 * pi * e**-1 * sqrt3),
    ("phi * pi^2 / e^2 * sqrt2", phi * pi**2 / e**2 * sqrt2),
    ("phi^3 * sqrt2 / (pi * e)", phi**3 * sqrt2 / (pi * e)),
    ("pi^2 * sqrt3 / (phi * e^2)", pi**2 * sqrt3 / (phi * e**2)),
    ("pi * phi / sqrt5", pi * phi / sqrt5),
    ("e^2 * sqrt2 / (phi * pi)", e**2 * sqrt2 / (phi * pi)),
    ("(phi/pi)^2 * e * sqrt3", (phi/pi)**2 * e * sqrt3),
]

print(f"Target: m_H/m_tau = {target_ht:.8f}")
for name, val in tests_mht:
    err = abs(val - target_ht) / target_ht * 100
    print(f"  {name:50s} = {val:.8f}  err={err:.3f}%")

# ============================================================
# Strategy 5: m_H ~ v / sqrt(2) * correction
# ============================================================
print(f"\n--- Strategy 5: Tree-level relation m_H vs v ---")
print(f"v = {v_vev} GeV")
print(f"v/sqrt(2) = {v_vev/math.sqrt(2):.4f} GeV")
print(f"m_H/(v/sqrt(2)) = {mH_exp/(v_vev/math.sqrt(2)):.8f}")
print(f"m_H * sqrt(2) / v = {mH_exp * math.sqrt(2) / v_vev:.8f}")
print(f"m_H/v = {mH_exp/v_vev:.8f}")
print(f"v/m_H = {v_vev/mH_exp:.8f}")
print(f"v/m_H approx = {v_vev/mH_exp:.6f}")

# The ratio v/m_H is interesting ~1.966
ratio_v_mh = v_vev / mH_exp
print(f"\nv/m_H = {ratio_v_mh:.8f}")
print(f"  phi^2 = {phi**2:.8f}  (err = {abs(phi**2 - ratio_v_mh)/ratio_v_mh*100:.3f}%)")
print(f"  phi + 1/phi = {phi + 1/phi:.8f}  (err = {abs(phi+1/phi - ratio_v_mh)/ratio_v_mh*100:.3f}%)")
print(f"  pi * phi / e = {pi*phi/e:.8f}  (err = {abs(pi*phi/e - ratio_v_mh)/ratio_v_mh*100:.3f}%)")
print(f"  e * phi / sqrt5 = {e*phi/sqrt5:.8f}  (err = {abs(e*phi/sqrt5 - ratio_v_mh)/ratio_v_mh*100:.3f}%)")
print(f"  sqrt(phi) * pi / sqrt2 = {math.sqrt(phi)*pi/sqrt2:.8f}  (err = {abs(math.sqrt(phi)*pi/sqrt2 - ratio_v_mh)/ratio_v_mh*100:.3f}%)")
print(f"  pi^2 / (phi * sqrt3) = {pi**2/(phi*sqrt3):.8f}  (err = {abs(pi**2/(phi*sqrt3) - ratio_v_mh)/ratio_v_mh*100:.3f}%)")
print(f"  phi * sqrt3 = {phi*sqrt3:.8f}  (err = {abs(phi*sqrt3 - ratio_v_mh)/ratio_v_mh*100:.3f}%)")

# ============================================================
# Summary of best candidates
# ============================================================
print("\n" + "=" * 70)
print("SUMMARY: BEST CANDIDATES FOR m_H HARMONIC EXPRESSION")
print("=" * 70)

# We know m_W has a relation to the weak coupling
# In SM: m_W = g * v / 2, m_Z = sqrt(g^2+g'^2) * v / 2, m_H = sqrt(lambda) * v
# If g, g', lambda can be expressed in Hn, then m_H follows

# Let's check if m_H relates to m_W and m_Z via harmonic ratios
print(f"\nm_W = {mW} GeV")
print(f"m_Z = {mZ} GeV")
print(f"cos(theta_W) = m_W/m_Z = {mW/mZ:.8f}")
print(f"cos(theta_W) target = {mW/mZ:.8f}")

# Is m_H/m_W harmonic?
# m_H/m_W = 125.20/80.377 = 1.5576...
# Is this somehow related to phi?
print(f"\nm_H/m_W = {mH_exp/mW:.8f}")
print(f"  phi = {phi:.8f}  (err = {abs(phi - mH_exp/mW)/(mH_exp/mW)*100:.3f}%)")
print(f"  pi/2 = {pi/2:.8f}  (err = {abs(pi/2 - mH_exp/mW)/(mH_exp/mW)*100:.3f}%)")
print(f"  e - 1 = {e-1:.8f}  (err = {abs(e-1 - mH_exp/mW)/(mH_exp/mW)*100:.3f}%)")
print(f"  sqrt(phi*pi) = {math.sqrt(phi*pi):.8f}  (err = {abs(math.sqrt(phi*pi) - mH_exp/mW)/(mH_exp/mW)*100:.3f}%)")
print(f"  phi*e/pi = {phi*e/pi:.8f}  (err = {abs(phi*e/pi - mH_exp/mW)/(mH_exp/mW)*100:.3f}%)")
print(f"  e*sqrt2/sqrt3 = {e*sqrt2/sqrt3:.8f}  (err = {abs(e*sqrt2/sqrt3 - mH_exp/mW)/(mH_exp/mW)*100:.3f}%)")
print(f"  phi^2/sqrt3 = {phi**2/sqrt3:.8f}  (err = {abs(phi**2/sqrt3 - mH_exp/mW)/(mH_exp/mW)*100:.3f}%)")

# m_H in GeV from a pure harmonic expression: need to find a reference scale
# The natural scale is v = 246.22 GeV
# m_H = v * f(Hn) where f is a harmonic function
# m_H/v = 0.5086... ~ 1/phi?
print(f"\nm_H/v = {mH_exp/v_vev:.8f}")
print(f"  1/phi = {1/phi:.8f}  (err = {abs(1/phi - mH_exp/v_vev)/(mH_exp/v_vev)*100:.3f}%)")
print(f"  1/sqrt(phi) = {1/math.sqrt(phi):.8f}  (err = {abs(1/math.sqrt(phi) - mH_exp/v_vev)/(mH_exp/v_vev)*100:.3f}%)")
print(f"  sqrt(phi)/e = {math.sqrt(phi)/e:.8f}  (err = {abs(math.sqrt(phi)/e - mH_exp/v_vev)/(mH_exp/v_vev)*100:.3f}%)")

# Maybe m_H = v * (e/pi) / sqrt3 ?
val = (e/pi) / sqrt3
print(f"  (e/pi)/sqrt3 = {val:.8f}  (err = {abs(val - mH_exp/v_vev)/(mH_exp/v_vev)*100:.3f}%)")

# Maybe m_H = v * sqrt(e/pi) / phi ?
val = math.sqrt(e/pi) / phi
print(f"  sqrt(e/pi)/phi = {val:.8f}  (err = {abs(val - mH_exp/v_vev)/(mH_exp/v_vev)*100:.3f}%)")

# m_H = v * (e/pi) * phi / sqrt3 ?
val = (e/pi) * phi / sqrt3
print(f"  (e/pi)*phi/sqrt3 = {val:.8f}  (err = {abs(val - mH_exp/v_vev)/(mH_exp/v_vev)*100:.3f}%)")

# m_H = v * sqrt(phi) / (pi/e) ?
val = math.sqrt(phi) / (pi/e)
print(f"  sqrt(phi)/(pi/e) = {val:.8f}  (err = {abs(val - mH_exp/v_vev)/(mH_exp/v_vev)*100:.3f}%)")

# Let's try two-step: first m_W, then m_H
print(f"\n\n--- Two-step approach via m_W ---")
# In SM: m_W = g * v / 2
# g = weak coupling, related to alpha_W = g^2/(4*pi)
alpha_W = 0.03408  # from PDG at M_Z scale
g_sq = 4 * pi * alpha_W
g = math.sqrt(g_sq)
print(f"alpha_W = {alpha_W}")
print(f"g = sqrt(4*pi*alpha_W) = {g:.6f}")
print(f"m_W from g*v/2 = {g*v_vev/2:.4f} GeV  (exp = {mW} GeV)")
print(f"(Recall: tree-level m_W prediction suffers from radiative corrections)")

# Try: m_H / m_W expressed harmonically
# Then m_H = m_W * harmonic_ratio
# If m_H/m_W ~ phi (1.5576 vs 1.6180, err = 3.88%)

# What about m_H = 2 * m_W / sqrt(phi) ?
val = 2 * mW / math.sqrt(phi)
print(f"\n2*m_W/sqrt(phi) = {val:.4f} GeV  (err = {abs(val-mH_exp)/mH_exp*100:.3f}%)")

# m_H = m_W * phi - m_Z * (phi-1) ? 
val = mW * phi - mZ * (phi - 1)
print(f"m_W*phi - m_Z*(phi-1) = {val:.4f} GeV  (err = {abs(val-mH_exp)/mH_exp*100:.3f}%)")

# Maybe m_H = m_Z * phi / sqrt2 ?
val = mZ * phi / sqrt2
print(f"m_Z*phi/sqrt2 = {val:.4f} GeV  (err = {abs(val-mH_exp)/mH_exp*100:.3f}%)")

# m_H = m_Z / sqrt(phi) ?
val = mZ / math.sqrt(phi)
print(f"m_Z/sqrt(phi) = {val:.4f} GeV  (err = {abs(val-mH_exp)/mH_exp*100:.3f}%)")

# m_H = m_W * sqrt(phi) ?
val = mW * math.sqrt(phi)
print(f"m_W*sqrt(phi) = {val:.4f} GeV  (err = {abs(val-mH_exp)/mH_exp*100:.3f}%)")

# ============================================================
# Conclusion
# ============================================================
print("\n" + "=" * 70)
print("CONCLUSION")
print("=" * 70)
print(f"""
The Higgs boson mass m_H = {mH_exp} GeV remains an OPEN PROBLEM
in the Harmonic Theory. No confirmed harmonic expression currently
exists with the <0.1% precision achieved for other constants.

Best candidate approaches:
1. m_H/v ~ 1/phi = 0.6180  (err ~21% - poor)
2. m_H/m_W ~ phi = 1.6180  (err ~3.88% - approximate)
3. v/m_H could relate to phi^2 or pi^2/(phi*sqrt3)
4. Two-step: express m_W in Hn first, then m_H via ratio

The harmonic framework predicts m_H SHOULD be expressible
as a product of Hn powers. This is a priority target for
future theoretical development (listed in implications.html).
""")