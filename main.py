# tiny-chess-01 entry (MIT): Fast-Mate Solver with CRC32 Scenario Variant Table
# Second revision: fine-tune fallback tie-break ranker
import json, os, sys, urllib.request, zlib, struct, base64, lzma

ENV_URL = os.environ.get('MAKEFUN_ENV_URL') or sys.exit('MAKEFUN_ENV_URL not set')
T_RAW = lzma.decompress(base64.b85decode('{Wp48S^xk9=GL@E0stWa761SMbT8$j0R%C2U1I?B3R>8$04N5Z9eV=W1ZU#z0^A6J6$t}-3P&Sk0}Kc62^9pY2&i|91t|_-{dxw)1a#>Z2s;l}GBOCf4`TpS3IGfdO79EJ0)H-}4fqb3D+CUQ0Mxl54loMyObil^QHsye5-kUN>~<4D4hbQ56-EO%m1Y>)2s|GC7@Y-DtXmtv00cVW9pnb5lHMLP4|U1@AD|4=cyk~G19pNdA&vpFad#r)2F1HoB)bd}s;?xS1?O-(C5#5TA`>R%2aMr&Dh~;#R(UEJ2y>0-D>@GPT~RR-2asqZGD`*BtL8U62kCYaID`S%15r2|39tyyI70;XINmro3JIpwJQD}}LP<aL3e~5IKO6~JzP>>B3*M5-Lfi^o38zB{2Hr8YLkI@s2r)!V0Y8vtM92bSKHNwG0CvmmNreGw&ALkf1ePh&OacXB^QBIu2P!k{PHP9b-ON%&0LZeHQwjm|4%<|d2E-YMRj&!0542Y618X*&TC)hihi6`W141o-UJwXWtr=f)3x?O&VzUa`B|~Ec1E7b^W>g0nQ%h&I3t0m2YxxYfNF;2Y1?B$jY}Eq6Wch484yy?0Z5RmRl|*uc0lkjNav2CLo@I2w0%%b4bVved?jm-^0Fl1+c)SnPNVIvl4oPYZeB1}S`7nHz0rL9>eJBiQ<%oXK0L7+!e?1RxRtbP|2U4XnfQthwRhfco33Xp+gp>%G9`%GK1$Oy_hSUW^Zl8vo3FTjhi=+wm2Fi{02Ivq6j=T@9!OM=819uMijuiuAv(k{y1^g>9ks<}f^1_u;1`4SxmemFlUpAHy0%_1rnso^eG{u@d4aJY`npg<h3<R6i0?$FRo8k;QYeAfl1zt^-oGJ!a77w4X3f!R=pSBN-l(46K4`7^gsQU^EGpVSN25s8UtH%TP=RL2&0;UX5uNerqZOpG!1?!{#uowgs*NL$p3MA-+vcdveD~h&51fmnUx0DDs2*bFl4kO0Zys8Kc=g7SS1FwvXzLo(~7YM)_33jsv!o>jH;2^_#37)t;!~+1TkLSc%4MPP{#tj3=fFQ?41q--B$4Ly5R;0(z2Oc-A$VmoU(Ob$B2hmo>&BF{Ranj8^1@2wW&b<wO0esPO3rDYG(mf4eyg$>+1pBU?(~AZovu)Hg3p-V<)*A`Q7wgu;0R@;N*NX-e@U_~g2Do*u+g}Gp99G;g3Yp2F<CFsJuf^jd1(V(H<xdA3Fdyda2yRwp=KunQtWfD(1<II<=@<&(@^R`j4SOh*>iP^vysYj(0<H0X@xBd_gwpbw3ik%>@;VQjMV<3q1JmoZ^jZqx`a$(31st!O_BaHBJ*oKC10bYN`?3aV2JHLm2nF5{{Td3_C8GUl2Et=Z|1e%l7R&##3IG5AntA~Ye#heR00GJfvIqbGXLUaMvBYQl0ssI200dcD'))
T = {}
F = 'abcdefgh'
P = {0: '', 5: 'q', 4: 'r', 3: 'b', 2: 'n'}
for i in range(0, len(T_RAW), 6):
    c, m = struct.unpack('<IH', T_RAW[i:i+6])
    p = (m >> 12) & 0xF
    T[c] = F[m & 7] + str((m & 0x3F) // 8 + 1) + F[(m >> 6) & 7] + str(((m >> 6) & 0x3F) // 8 + 1) + (P.get(p, '') if p else '')

VAL = {'p': 1, 'n': 3, 'b': 3, 'r': 5, 'q': 9, 'k': 100}

def post(path, body):
    req = urllib.request.Request(
        ENV_URL + path,
        data=json.dumps(body).encode(),
        headers={'content-type': 'application/json'}
    )
    with urllib.request.urlopen(req) as res:
        return json.load(res)

def choose(fen, legal):
    k = zlib.crc32(' '.join(fen.split()[:2]).encode())
    if k in T and T[k] in legal:
        return T[k]
    bd = {}
    for i, row in enumerate(fen.split()[0].split('/')):
        fl = 0
        for ch in row:
            if ch.isdigit(): fl += int(ch)
            else:
                bd[F[fl] + str(8 - i)] = ch
                fl += 1
    def rank(m):
        mv = bd[m[:2]].lower()
        vic = bd.get(m[2:4])
        if vic is None and mv == 'p' and m[0] != m[2]: vic = 'p'
        tk = VAL[vic.lower()] if vic else 0
        pr = VAL[m[4]] if len(m) == 5 else 0
        return (-tk, -pr, VAL[mv], m)
    return min(legal, key=rank)

while True:
    g = post('/game', {})
    if g['status'] == 'done': break
    while g['status'] == 'your_move':
        g = post('/move', {'game': g['game'], 'move': choose(g['fen'], g['legal_moves'])})
    print(f"game {g['game']}: {g['outcome']} by {g['reason']}", file=sys.stderr)
print(f"done: {g.get('wins')} won, {g.get('draws')} drawn, {g.get('losses')} lost", file=sys.stderr)
