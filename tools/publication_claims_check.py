"""Active publication checks, distinct from the archived edition's legacy gates."""
from pathlib import Path
import json,hashlib,re
from manuscript_reference_audit import expand_source,semantic_errors
ROOT=Path(__file__).resolve().parents[1]
def check_publication():
    errors=[];ledger=json.loads((ROOT/'output/review-revision/2026-10-07-checks/publication-ledger.json').read_text())
    for name,digest in ledger['artifact_sha256'].items():
        if hashlib.sha256((ROOT/'hazard/data'/name).read_bytes()).hexdigest()!=digest:errors.append('Stale ledger artifact '+name)
    source=expand_source(ROOT/'paper/final/paper_final_v1.tex');long=expand_source(ROOT/'paper/final/paper_final_v1_long_abstract.tex')
    errors+=semantic_errors(source)+semantic_errors(long)
    if source.split(r'\end{abstract}',1)[1]!=long.split(r'\end{abstract}',1)[1]:errors.append('Edition body drift')
    for c in ledger['claims']:
        if abs(c['billions']/ledger['benchmark_b']*100-c['points'])>1e-9:errors.append('Dollar/point mismatch '+c['label'])
        if f"{c['points']:.4f}" not in source or f"{c['billions']:.4f}" not in source:errors.append('Missing exact scenario row '+c['label'])
    if len(re.findall(r'\\section\{',expand_source(ROOT/'paper/final/journal_main_v2.tex')))!=6:errors.append('Main section count')
    # Verify the requested destinations describe the intended objects, not only their types.
    for label,token in [('eq:beta1','q(P(1-d))'),('eq:pathB','h^R_{it}'),('eq:default','0.0003'),('tab:wal','weighted-average life')]:
        pos=source.find(r'\label{'+label+'}');local=source[max(0,pos-500):pos+500]
        if token not in local:errors.append('Wrong semantic content '+label)
    for obsolete in ['above-cap reinvestment never','h^{\\mathrm{add}}_{it}=f_t+h^{R}_{it}','31 origination-quarter']:
        if obsolete in source:errors.append('Retired live claim '+obsolete)
    for name in ['review_results_table','review_population_table','review_validation_table','review_validation_detail','review_support_table']:
        if not (ROOT/'paper/final'/f'{name}.tex').exists():errors.append('Missing generated table '+name)
    stock=ledger['stock_flow'];valid=ledger['validation_aggregate']
    if not stock['production_parity_pass']:errors.append('Production parity failed')
    if valid['on']['weighted_rmse_monthly_pp']<=valid['base']['weighted_rmse_monthly_pp']:errors.append('Recorded adverse validation changed; manuscript needs review')
    abstract=source.split(r'\begin{abstract}',1)[1].split(r'\end{abstract}',1)[0]
    words=len(re.findall(r"[A-Za-z0-9]+(?:[-'][A-Za-z0-9]+)*",re.sub(r'\\[A-Za-z]+','',abstract)))
    if not 180<=words<=220:errors.append(f'Abstract word target: {words}')
    return errors
if __name__=='__main__':
    e=check_publication();print(json.dumps({'errors':e},indent=2));raise SystemExit(bool(e))
