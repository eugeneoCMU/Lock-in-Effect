"""Generate current tables and exact claims ledger from frozen result artifacts."""
from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parents[1];DATA=ROOT/'hazard/data';TEX=ROOT/'paper/final'
used={}
def read(name):
 p=DATA/name;used[name]=hashlib.sha256(p.read_bytes()).hexdigest();return json.loads(p.read_text())
def table(caption,label,cols,header,rows):
 return '\\begin{table}[H]\n\\centering\\small\n\\caption{'+caption+'}\n\\label{'+label+'}\n\\begin{tabular}{@{}'+cols+'@{}}\\toprule\n'+header+'\\\\\\midrule\n'+'\n'.join(r+'\\\\' for r in rows)+'\n\\bottomrule\n\\end{tabular}\n\\end{table}\n'
move=read('moving_share_bracket_offwindow_results.json');psa=read('psa_level_sweep_results.json');form=read('floor_form_offwindow_results.json');stock=read('stock_flow_accounting_2026-10-07_results.json');bridge=read('coupon_bridge_2026-10-07_results.json');saved=read('saved_joint_accounting_2026-10-07_results.json');valid=read('pathb_validation_2026-10-07_results.json')
assert move['parity_gates_all_pass'] and psa['parity_gates_all_pass'] and stock['production_parity_pass']
rows=['Moving share 0 (definitional) & 0.0000 & 0.0000']
claims=[]
for s in ['0.25','0.5','1']:
 r=move['cells'][s];rows.append(f'Moving share {100*float(s):g}\\% & {r["marginal_pp"]:.4f} & {r["marginal_b"]:.4f}');claims.append({'label':'moving share '+s,'points':r['marginal_pp'],'billions':r['marginal_b'],'artifact':'moving_share_bracket_offwindow_results.json','key':'cells.'+s})
rows.append('\\addlinespace')
for s in [75,100,125,150]:
 r=psa['cells'][f'4.991|{s}|6.5'];rows.append(f'{s} PSA & {r["marginal_pp"]:.4f} & {r["marginal_b"]:.4f}');claims.append({'label':str(s)+' PSA','points':r['marginal_pp'],'billions':r['marginal_b'],'artifact':'psa_level_sweep_results.json','key':f'cells.4.991|{s}|6.5'})
r=next(x for x in form['rows'] if x['form']=='additive' and x['floor_annual_cpr_pct']==4.991)['band']['6.5']
rows+=['\\addlinespace',f'Survival-combination form & {r["marginal_pp"]:.4f} & {r["marginal_b"]:.4f}']
claims.append({'label':'survival combination','points':r['marginal_pp'],'billions':r['marginal_b'],'artifact':'floor_form_offwindow_results.json','key':'additive,4.991,6.5'})
(TEX/'review_results_table.tex').write_text(table('Hard-maximum anchor and separate assumption comparisons. Unless varied: saved sample, 4.991\\% annual floor, 100 PSA, full moving share, maximum form, observed-holdings flow reporting. Marginal is cumulative reported principal off minus on, June 2022--November 2025. Points equal $100\\times$ marginal/\\$764.748253B; no row is a confidence interval.','tab:mainresults','p{8cm}rr','Assumption & Marginal (points) & Marginal (\\$B)',rows))
rows=[]
for name,r in [('Saved production sample',stock),('Saved sample, joint cells',saved),('Fresh survivors, 80 bp',bridge['bridges']['80']['paired_results'])]:
 p=r['paths']['production'];c=r['paths']['closed'];rows.append(f'{name} & {p["marginal_b"]:.4f} & {c["marginal_b"]:.4f} & {c["marginal_pct_initial_active"]:.4f}')
(TEX/'review_population_table.tex').write_text(table('Three named populations and two reporting conventions. Dollar columns expand each pool to total initial holdings. The last column is closed-book marginal principal per \\$100 initial active pool balance, not a measured supported-slice contribution.','tab:populationresults','p{5.5cm}rrr','Sample & Reported (\\$B) & Closed (\\$B) & Per \\$100',rows))
rows=[]
for label,key in [('2023 cohort-speed baseline','base'),('Response off','off'),('Response on','on')]:
 r=valid['aggregate'][key];rows.append(f'{label} & {r["predicted_b"]:.3f} & {r["ratio"]:.3f} & {r["weighted_rmse_monthly_pp"]:.4f}')
(TEX/'review_validation_table.tex').write_text(table('Retrospective conditional prediction, January 2024--September 2025. Observed prepaid principal is \\$131.303 billion across 5,019 cohort-months. Dollars use observed Freddie exposure. RMSE is exposure-weighted, in monthly probability percentage points.','tab:validation','p{6cm}rrr','Candidate & Predicted (\\$B) & P/O & RMSE',rows))
rows=[]
for period,m in valid['subperiods'].items():
 rows.append(f'{period} & {m["base"]["observed_b"]:.3f} & '+ ' & '.join(f'{m[k]["ratio"]:.3f} / {m[k]["weighted_rmse_monthly_pp"]:.4f}' for k in ['base','off','on']))
s=table('Fixed evaluation subperiods: prediction/observation ratio and monthly weighted RMSE. The final half-year ends September 2025.','tab:validperiods','lrrrr','Period & Observed (\\$B) & Baseline P/O; RMSE & Off P/O; RMSE & On P/O; RMSE',rows)
s+='\n{\\small\n\\begin{longtable}{@{}lrrrrr@{}}\n\\caption{Coupon-vintage validation totals. Ratios retain all candidates on the same cells; dollars are observed prepaid principal.}\\label{tab:validcells}\\\\\n\\toprule\nVintage; note coupon & Rows & Observed (\\$B) & Baseline P/O & Off P/O & On P/O\\\\\\midrule\n\\endfirsthead\n\\toprule\nVintage; note coupon & Rows & Observed (\\$B) & Baseline P/O & Off P/O & On P/O\\\\\\midrule\n\\endhead\n'
for key,m in valid['coupon_vintage'].items():
 vintage,coupon=key.split('|');ratios=['--' if m[k]['ratio'] is None else f'{m[k]["ratio"]:.3f}' for k in ['base','off','on']]
 obs=m['base']['observed_b']; shown='$<0.001$' if 0<obs<.001 else f'{obs:.3f}'
 s+=f'{vintage}; {float(coupon)*100:g}\\% & {m["base"]["n"]} & {shown} & '+' & '.join(ratios)+'\\\\\n'
s+='\\bottomrule\n\\end{longtable}\n}\n';(TEX/'review_validation_detail.tex').write_text(s)
target=read('joint_soma_pair_results.json')['target_cells'];rows=[]
for key,share in target.items():
 c,v=key.split('|');counts=[bridge['bridges'][str(b)]['cell_counts'][key] for b in [60,80,100]]
 rows.append(f'{float(c)*100:g}\\%; {v.replace("-","--")} & {share*100:.3f}\\% & '+' & '.join(str(n) for n in counts))
(TEX/'review_support_table.tex').write_text(table('Fixed-ID bridge support. Target shares condition on the twelve listed cells; their total face share is 47.5876\\%. All targets match within $5.6\\times10^{-17}$ at initialization.','tab:support','lrrrr','Pass-through; vintage & Target & 60 bp loans & 80 bp loans & 100 bp loans',rows))
for r in claims:assert abs(r['billions']/764.7482532227002*100-r['points'])<1e-10
out={'benchmark_b':764.7482532227002,'claims':claims,'artifact_sha256':used,'stock_flow':stock,'population_bridge':bridge,'validation_aggregate':valid['aggregate']}
(ROOT/'output/review-revision/2026-10-07-checks/publication-ledger.json').write_text(json.dumps(out,indent=2)+'\n')
print('Generated six tables and exact publication ledger')
