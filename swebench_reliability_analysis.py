"""Reproducibility script for the chapter
"Measuring AI Agents: Validity, Reliability, and What Leaderboards Hide".

NATURE OF THE ANALYSIS: secondary statistical analysis of publicly released results.
No agent was executed and no patch was re-evaluated by the authors; all task outcomes were
produced by the original submitters with the SWE-bench evaluation harness and published in
https://github.com/SWE-bench/experiments . The authors' contribution is the analysis below.

DATA: repository commit 40f164d5b8f1d249bf95a6df8b74b577fd8e519d (committed 2026-09-03T01:24:30Z).
Usage:  python swebench_reliability_analysis.py               # uses frozen snapshot in ./data
        python swebench_reliability_analysis.py --rebuild     # re-downloads the pinned commit
Requires: python>=3.10, numpy, pandas, scipy, statsmodels, requests, pyyaml
"""
import os, sys, io, json, hashlib, zipfile, numpy as np, pandas as pd, yaml
from scipy.stats import binomtest, kendalltau
from scipy.optimize import minimize
from scipy.special import expit
from statsmodels.stats.proportion import proportion_confint
SHA="40f164d5b8f1d249bf95a6df8b74b577fd8e519d"; S7=SHA[:7]; N=500
MAT=f"data/swebench_verified_outcomes_{S7}.csv"; LOG=f"data/submission_log_{S7}.csv"; ZIP=f"data/raw_files_{S7}.zip"
EXPECTED_SHA256="433e345cf40b88e26e1f16d686ef18cdc645ee52157b468f6f800ea59c2ad847"
HARMONISE={"claude-4-sonnet-20250514":"claude-sonnet-4-20250514"}

def rebuild():
    import requests
    from concurrent.futures import ThreadPoolExecutor
    raw=f"https://raw.githubusercontent.com/SWE-bench/experiments/{SHA}/evaluation/verified"
    subs=sorted(d["name"] for d in requests.get(f"https://api.github.com/repos/SWE-bench/experiments/contents/evaluation/verified?ref={SHA}",timeout=60).json() if d["type"]=="dir")
    def g(s):
        out={}
        for name in ["results/results.json","metadata.yaml","per_instance_details.json"]:
            r=requests.get(f"{raw}/{s}/{name}",timeout=60); out[name]=r.content if r.status_code==200 else None
        return s,out
    with ThreadPoolExecutor(8) as P: files=dict(P.map(g,subs))
    inc=[s for s in subs if files[s]["results/results.json"]]
    tasks=sorted(json.loads(next(f["per_instance_details.json"] for f in files.values() if f["per_instance_details.json"])).keys())
    res={s:set(json.loads(files[s]["results/results.json"])["resolved"]) for s in inc}
    M=pd.DataFrame([[int(t in res[s]) for t in tasks] for s in inc],index=inc,columns=tasks); M.index.name="submission"
    os.makedirs("data",exist_ok=True); M.to_csv(MAT)
    with zipfile.ZipFile(ZIP,"w",zipfile.ZIP_DEFLATED) as z:
        for s in subs:
            for name,arc in [("results/results.json","results/results.json"),("metadata.yaml","metadata.yaml")]:
                if files[s][name]: z.writestr(f"evaluation/verified/{s}/{arc}",files[s][name])

def load_meta():
    meta={}
    with zipfile.ZipFile(ZIP) as z:
        for n in z.namelist():
            if n.endswith("metadata.yaml"): meta[n.split("/")[2]]=yaml.safe_load(z.read(n)) or {}
    return meta

def mcnemar(a,b):
    b01=int(((a==1)&(b==0)).sum()); b10=int(((a==0)&(b==1)).sum()); n=b01+b10
    return 1.0 if n==0 else binomtest(b01,n,0.5).pvalue

def main():
    if "--rebuild" in sys.argv or not os.path.exists(MAT): rebuild()
    digest=hashlib.sha256(open(MAT,"rb").read()).hexdigest()
    print("outcome matrix sha256:",digest,"(matches chapter snapshot)" if digest==EXPECTED_SHA256 else "(DIFFERS from chapter snapshot)")
    D=pd.read_csv(MAT,index_col=0); subs=list(D.index); M=D.values; score=M.mean(1)
    print(f"{len(subs)} submissions x {M.shape[1]} tasks; tasks resolved by no included submission: {int((M.sum(0)==0).sum())}")
    o=np.argsort(-score,kind="stable"); Ms=M[o]; ss=score[o]
    # E1 statistical resolution
    padj=np.array([mcnemar(Ms[i],Ms[i+1]) for i in range(len(Ms)-1)])
    pt=np.array([mcnemar(Ms[i],Ms[j]) for i in range(20) for j in range(i+1,20)])
    lo,hi=proportion_confint(np.round(ss*N),N,method="wilson")
    print(f"E1 adjacent pairs not significant: {(padj>=.05).sum()}/{len(padj)}; top-20 pairs not significant: {(pt>=.05).sum()}/{len(pt)}; median gap {np.median(-np.diff(ss))*100:.1f} pp; median CI half-width {np.median((hi-lo)/2)*100:.1f} pp")
    # E2 task bootstrap
    rng=np.random.default_rng(0); K=15; ranks=np.zeros((2000,K),int)
    for b in range(2000):
        idx=rng.integers(0,N,N); sc=Ms[:K,idx].mean(1); ranks[b]=np.argsort(np.argsort(-sc+rng.normal(0,1e-9,K)))+1
    print("E2 P(rank 1) for observed ranks 1-3:",(ranks==1).mean(0)[:3].round(3))
    # E3 Rasch-model repeated-run simulation (model-based, illustrative)
    A=M.shape[0]; lam=0.05
    def f(x):
        th,b=x[:A],x[A:]; P=expit(th[:,None]-b[None,:]); ll=(M*np.log(P+1e-12)+(1-M)*np.log(1-P+1e-12)).sum(); g=M-P
        return -(ll-lam/2*(th@th+b@b)), -np.concatenate([g.sum(1)-lam*th,-g.sum(0)-lam*b])
    x=minimize(f,np.zeros(A+N),jac=True,method="L-BFGS-B",options={"maxiter":3000}).x
    P=expit(x[:A,None]-x[None,A:]); Pt=P[np.argsort(-P.mean(1))[:20]]; rng=np.random.default_rng(1)
    for k in [1,3,5,10]:
        taus=[];sw=[]
        for _ in range(2000):
            sc=rng.binomial(k,Pt).mean(1)/k; r=np.argsort(-sc+rng.normal(0,1e-9,20)); pos=np.argsort(r)
            taus.append(kendalltau(pos,np.arange(20))[0]); sw.append(np.mean(pos[1:]<pos[:-1]))
        print(f"E3 runs/task={k}: Kendall tau={np.mean(taus):.3f}, adjacent inverted={np.mean(sw):.3f}")
    # E4 attribution (metadata, as reported by submitters)
    meta=load_meta(); att=[]; m1=[]
    for s in subs:
        tags=(meta.get(s) or {}).get("tags") or {}; sysd=tags.get("system") if isinstance(tags.get("system"),dict) else {}
        a=str(sysd.get("attempts")); att.append({"1":"1","2":"2+","2+":"2+"}.get(a,"unreported"))
        mods=tags.get("model") or []; mods=mods if isinstance(mods,list) else [mods]
        m1.append(HARMONISE.get(mods[0],mods[0]) if len(mods)==1 else None)
    T=pd.DataFrame({"score":score,"att":att,"m1":m1},index=subs)
    print("E4 attempts reported:",T.att.value_counts().to_dict())
    g=T.dropna(subset=["m1"]).groupby("m1").score.agg(["count","min","max"]); g=g[g["count"]>=3]
    for m,r in g.iterrows(): print(f"E4 {m}: n={int(r['count'])}, {r['min']*100:.1f}-{r['max']*100:.1f}% (range {(r['max']-r['min'])*100:.1f} pp)")
    # E5 task informativeness
    sol=Ms[:20].sum(0); pr=M.mean(0)
    print(f"E5 top-20: solved by all {(sol==20).sum()}, by none {(sol==0).sum()}, discriminating {((sol>0)&(sol<20)).sum()}; tasks with 30-70% pass rate: {((pr>=.3)&(pr<=.7)).sum()}")

if __name__=="__main__": main()
