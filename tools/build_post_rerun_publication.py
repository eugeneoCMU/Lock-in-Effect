"""Generate publication additions from sealed corrected rerun and diagnostic outputs."""
from pathlib import Path
import argparse,json,hashlib
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]

def load(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def build(root,analysis):
    root,analysis=Path(root),Path(analysis)
    complete=load(analysis/'completed.json');assert complete['status']=='complete'
    for name,expected in complete['output_sha256'].items():assert sha(analysis/name)==expected,name
    matrix=root/'mixture-comparison-verified-session';accepted=load(matrix/'acceptance.json');assert accepted['status']=='passed'
    result=load(matrix/'results.json');combined=load(root/'combined/report.json');bridge=load(analysis/'bridge.json');infer=load(analysis/'floor_inference.json');mapping=load(analysis/'floor_mapping.json');fit=load(analysis/'fit_review.json')
    models=[('Hard maximum',result['benchmark_pair'],load(matrix/'benchmark-scoring/results.json'),'original_on'),
        ('Additive survival',result['additive_benchmark_pair'],load(matrix/'additive-benchmark-scoring/results.json'),'additive_on')]
    for mode,label in [('inherited_psa','Mixture: inherited reference'),('matched_max_off','Mixture: matched OFF')]:
        name=f'{mode}-illustrative-positive_only-share-0.75';models.append((label,load(matrix/(name+'-pair/results.json')),load(matrix/(name+'-scoring/results.json')),'mixture_on'))
    rows=[]
    for label,pair,score,key in models:
        m=score['aggregate'][key];rows.append(f"{label} & {pair['reported_marginal_b']:.2f} & {pair['closed_pool_cash_marginal_b']:.2f} & {m['weighted_rmse_monthly_pp']:.5f} " + r'\\')
    baseline=models[0][2]['aggregate']['base'];primary=infer['stratum'];month=infer['month']
    table=r'''\begin{table}[H]
\centering\small
\caption{Completed corrected-input comparisons. Principal differences are response OFF minus ON, June 2022--November 2025 (\$ billions); RMSE is the exposure-weighted monthly payoff-rate error on January 2024--September 2025 (percentage points).}\label{tab:correctedresults}
\begin{tabular}{@{}p{5.4cm}rrr@{}}\toprule
Specification & Reported & Pool cash & ON RMSE\\\midrule
@ROWS@
\bottomrule\end{tabular}
\begin{minipage}{0.94\textwidth}\footnotesize
Both mixture rows assume a75\% sensitive share, positive-gap-only suppression, and$\gamma=-\log(0.935)$ per percentage point. References are inherited, not newly calibrated. Reported principal uses each leg's monthly observed-holdings scale; pool cash sums unscaled simulated principal. Simple-baseline RMSE is@BASE@; none of these ON models outperforms it. These amounts are conditional model sensitivities, not interval endpoints or identified SOMA effects.
\end{minipage}
\end{table}
'''.replace('@ROWS@','\n'.join(rows)).replace('@BASE@',f"{baseline['weighted_rmse_monthly_pp']:.5f}")
    section=r'''\subsection{Completed corrected-source rerun}\label{sec:corrected}
The October 14 rerun verifies all twenty Freddie source partitions for2017Q1--2021Q4 and reconstructs the same outcome cutoff ofSeptember 2025. Eligibility now explicitly requires an original360-month fixed-rate contract, valid original borrower attributes, positive note rate and principal. The source frame contains9,516,603 eligible originals and6,261,246 observed May2022 survivors; the fixed simulation draw contains75,000 unique loan IDs. Native and Release47 layouts retain separate per-quarter provenance. Fifty-seven loans, totaling\$21.870 million in original principal, have unknown pre-May histories. Their later observations remain in the panel; no missing early payoff is imputed, and none enters the May starting portfolio. Fixed original-cohort denominators, known-history initialization and assumption-dependent burnout bounds are audited separately.

With the inherited4.991\% annual hard-maximum floor,100PSA, full responsive share and imported response unchanged, the corrected pair produces\$16.2155 billion in reported principal difference, or\$14.3407 billion in closed-pool cash accounting. This is an inherited-parameter audit benchmark, not a newly estimated optimal specification. The historical\$42.6084 billion calculation remains a version-specific result. The controlled substitutions in Appendix~\ref{app:correcteddiagnostics} separate sample/composition, historical initialization and transition inputs as far as archived fields permit; they do not identify an isolated parser effect.

The full prespecified matrix contains forty mixture scenarios: five assumed shares, two response conversions, two gap treatments and two reference schedules. Both maximum and additive-survival benchmarks are retained. All84 paired/scoring outputs pass common-input, support, hash and principal-accounting checks. Matched-reference OFF paths reproduce the hard-maximum OFF benchmark, and positive-gap-only zero-share paths satisfy the ON/OFF identity. These checks establish computational comparability rather than scientific identification. Table~\ref{tab:correctedresults} reports the illustrative75\% cases and both benchmarks.

@TABLE@

On identical4,998 cohort-month observations in238 cells, corrected observed voluntary payoff is\$107.8634 billion. The inherited-reference75\% mixture predicts\$113.3676 billion; the matched-reference case predicts\$118.9830 billion. The former is closer to the observed total, while the latter has lower cohort-month RMSE and MAE. Both improve on the hard-maximum and additive ON errors, but both remain worse than the simple cohort-speed baseline. The separately recorded3.5\% floor/100PSA candidate predicts\$106.6200 billion with RMSE0.11060 and MAE0.08264 percentage points on these corrected rows. Its parameters were selected on the preserved2023 development inputs, not retuned here; it also remains worse than the baseline, and its scores do not promote it into the paired benchmark. Coupon--vintage and half-year errors are disclosed in Appendix~\ref{app:correcteddiagnostics}; these previously examined outcomes do not select a preferred reference or share.

Fresh floor inference uses corrected2018 discount-cohort data rather than transferring historical bands. It retains the inherited end-exposure payoff-speed ratio and imported response interpretation. Its measurement uncertainty, numerical effect mapping, cluster sensitivity and limited age support are reported in Appendix~\ref{app:correcteddiagnostics}. Assumed mixture shares and reference choices remain structural sensitivities, not statistical confidence intervals. Source verification does not identify a sale/refinance decomposition, a causal imported response, a representative SOMA sample or an untouched forward evaluation.

\begin{figure}[H]\centering
\includegraphics[width=0.96\textwidth]{fig14_corrected_comparison.png}
\caption{Corrected-input conditional differences and retrospective errors. Both mixture cases assume75\% sensitivity and the illustrative positive-gap response. Reported and pool-cash dollars are distinct accounting measures; the baseline is a prediction comparator, not a lock-in counterfactual.}\label{fig:correctedcomparison}
\end{figure}
'''.replace('@TABLE@',table)
    # Tables retain each group's full observed/support values in fit_review.json.
    half=[r for r in fit['rows'] if r['group']=='halfyear']
    groupnames=sorted({r['cell'] for r in half});labels={'max':'Max','additive':'Additive','mixture-inherited-75':'Inherited75','mixture-matched-75':'Matched75'}
    halfrows=[]
    for group in groupnames:
        d={r['model']:r for r in half if r['cell']==group};base=d['max']
        halfrows.append(f"{group} & {base['observed_b']:.2f} & {base['baseline_rmse']:.4f} & "+' & '.join(f"{d[k]['weighted_rmse_monthly_pp']:.4f}" for k in labels)+r'\\')
    bnames=['Archived inputs/current engine','Corrected sample; legacy history','Corrected history; archived transitions','All corrected inputs']
    brows=[]
    for i,s in enumerate(bridge['stages']):
        delta='--' if i==0 else f"{bridge['sequential_changes_b'][i-1]:+.4f}"
        brows.append(f"{bnames[i]} & {s['reported_marginal_b']:.4f} & {s['cash_marginal_b']:.4f} & {delta} "+r'\\')
    floorrows=[]
    for name,d in [('Stratum',primary),('Month',month)]:
        interval='Not bounded' if not d['computable'] else f"[{d['floor_cpr_ci95_pct'][0]:.3f}, {d['floor_cpr_ci95_pct'][1]:.3f}]"
        floorrows.append(f"{name} & {d['n_clusters']} & {d['effective_clusters']:.2f} & {d['max_leverage']:.3f} & {interval} "+r'\\')
    maptext='No bounded dollar interval is reported: the floor inversion or mapping verification does not support one.'
    if mapping['accepted_approximation']:
        lo,hi=mapping['mapped_measurement_band_b'];maptext=(f"The corrected-engine PCHIP image of the primary retained floor set gives an approximate reported measurement band of\\${lo:.2f}--\\${hi:.2f} billion. {len(mapping['grid'])} exact paired grid runs and {len(mapping['holdout_checks'])} midpoint checks have maximum holdout discrepancy\\${mapping['max_holdout_error_b']:.4f} billion, below the prespecified\\$0.05 billion numerical tolerance. The checked grid is monotone; this numerical audit is not a proof of global exact coverage. The exact point-read effect is\\${mapping['point_mapped_marginal_b']:.2f} billion and is a reanchored scenario, distinct from the inherited4.991\\% benchmark. This band conditions on the fixed sample, response, hazard form, initialization, transition inputs and reporting rule; it excludes mixture-share, reference, elasticity, seasoning and portfolio-transport uncertainty.")
    wins={key:sum(r['rmse_change_from_baseline']<0 for r in fit['rows'] if r['group']=='coupon_vintage' and r['model']==key) for key in labels}
    appendix=r'''\section{Corrected-Input Diagnostics}\label{app:correcteddiagnostics}
\subsection{Sequential input comparison}
The historical anchor is\$42.6083939 billion. Replaying archived inputs through the current engine gives\$@ARCH@ billion, leaving a\$@RESID@ billion replication residual. That residual is retained, not assigned to source parsing. Archived loan records lack original-term and pre-May history fields. Their compatibility replay therefore retains the original assumed360-month amortization and zero-history initialization; it does not certify their original terms. The archived transition proxy has zero rows for unsupported states, whose states remain unchanged under the documented legacy rule. The final corrected stage instead requires audited terms, history and identified pre-QT transitions.

\begin{table}[H]\centering\small
\caption{Sequential controlled substitutions (\$ billions). Changes depend on the stated order and are not causal contributions.}\label{tab:correctedbridge}
\begin{tabular}{@{}p{5.7cm}rrr@{}}\toprule
Input stage & Reported & Pool cash & Change\\\midrule
@BRIDGE@
\bottomrule\end{tabular}\end{table}

The sample substitution jointly changes eligibility, draw, covariates, observed balances and states; it is not isolated random sampling variation. The history substitution retains the corrected sample and archived transition proxy while installing observed pre-May burnout and fixed-cohort denominator multipliers. The final transition substitution reproduces the accepted corrected benchmark within$10^{-8}$ billion dollars. This sequential comparison cannot disentangle every source correction or recover unavailable archived fields.

\subsection{Disaggregated retrospective fit}
All four models use identical observed outcomes and exposure in44 coupon--vintage groups and four half-year groups. The complete group-level support, predicted totals, ratios, signed errors, RMSE and MAE are retained in\path{fit_review.json}; low-exposure groups are retained rather than silently discarded. Against the simple baseline's group RMSE, the max, additive, inherited75\% and matched75\% models improve in@WINS@ groups, respectively, out of44. Counts are unweighted diagnostics; aggregate errors remain exposure weighted. Half-year scores retain the shortenedJuly--September2025 period explicitly.

\begin{table}[H]\centering\scriptsize
\caption{Same-support half-year payoff errors. Observed principal is\$ billions; all errors are exposure-weighted monthly-rate RMSE in percentage points.}\label{tab:correctedhalves}
\begin{tabular}{@{}lrrrrrr@{}}\toprule
Period & Observed & Baseline & Max & Additive & Inherited75 & Matched75\\\midrule
@HALVES@
\bottomrule\end{tabular}\end{table}

\subsection{Fresh floor measurement uncertainty}
The selected2018 note-minus-market gap is at most$-25$ basis points and mean loan age is at least twelve months. Corrected support contains@N@ cohort-months in@G@ strata and@MONTHS@ calendar months. The point annualized end-exposure payoff-speed ratio is@POINT@\%. Selected mean ages range from12.000 to18.959 months; no qualifying cohort has mean age at least24 months. Support isJune--December2018. A cohort mean-age threshold does not establish each loan's age, and this ratio is not an observed beginning-balance hazard or a purely involuntary exit rate.

Restricted Webb test inversion uses9,999 six-point-weight draws, seed42, and401 candidate monthly ratios over the observed point plus/minus five CR1 standard errors. The same weights are reused across candidates. The observed statistic uses the inherited unrestricted CR1 studentizer; each null-imposed resample recomputes its restricted studentizer. Nonphysical candidates are excluded explicitly; finite-studentizer counts, retained indices, contiguity and open-edge flags are archived. Stratum clustering permits repeated-month dependence within the original four-way cohort; month clustering instead addresses a common month shock. Neither alone is two-way clustering or an identified total-uncertainty model.

\begin{table}[H]\centering\small
\caption{Corrected floor-ratio inference. Nominal clusters, exposure-effective count, maximum leverage, and annualized retained95\% candidate interval.}\label{tab:correctedfloor}
\begin{tabular}{@{}lrrrr@{}}\toprule
Cluster & Nominal & Effective & Max leverage & Floor(\%)\\\midrule
@FLOORS@
\bottomrule\end{tabular}\end{table}

@MAPPING@

The historical$+1.9$--$+9.1$ point band belongs to the archived floor read, sample and mapping and is not transferred to the corrected benchmark. The new floor inference does not estimate a sensitive share or provide statistical coverage for the40 structural scenarios. All results condition on previously inspected source and evaluation data; no prospective validation or full-SOMA causal interpretation follows.
'''
    appendix=appendix.replace('@ARCH@',f"{bridge['stages'][0]['reported_marginal_b']:.7f}").replace('@RESID@',f"{bridge['current_engine_archived_residual_b']:.7f}").replace('@BRIDGE@','\n'.join(brows)).replace('@HALVES@','\n'.join(halfrows)).replace('@FLOORS@','\n'.join(floorrows)).replace('@N@',str(primary['n_rows'])).replace('@G@',str(primary['n_clusters'])).replace('@MONTHS@',str(month['n_clusters'])).replace('@POINT@',f"{primary['point_cpr_pct']:.4f}").replace('@MAPPING@',maptext).replace('@WINS@','/'.join(str(wins[k]) for k in labels))
    # Minimal typography correction for composed numeric tokens.
    import re
    def tidy(s):
        s=re.sub(r'([A-Za-z])(\\\$)',r'\1 \2',s)
        s=re.sub(r'(?<=[A-Za-z])(?=[0-9$])',' ',s);s=re.sub(r'(?<=[0-9])(?=[A-Za-z])',' ',s)
        s=s.replace('ofSeptember','of September').replace('and6,','and 6,').replace('in238','in 238').replace('in44','in 44').replace('out of44','out of 44').replace('fromJuly','from July').replace('shortenedJuly','shortened July')
        s=s.replace('fig 14_corrected_comparison','fig14_corrected_comparison')
        return re.sub(r'(\d{4}) Q ([1-4])',r'\1Q\2',s)
    final=ROOT/'paper/final';(final/'corrected_results.tex').write_text(tidy(section));(final/'corrected_diagnostics.tex').write_text(tidy(appendix))
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42})
    fig,(ax,bx)=plt.subplots(2,1,figsize=(6.5,7.1))
    x=np.arange(4);names=['Hard max','Additive','Mixture\ninherited','Mixture\nmatched OFF']
    ax.bar(x-.18,[p['reported_marginal_b'] for _,p,_,_ in models],.36,label='Reported, monthly holdings scale',color='#4477AA')
    ax.bar(x+.18,[p['closed_pool_cash_marginal_b'] for _,p,_,_ in models],.36,label='Closed-pool principal cash',color='#BBBBBB')
    ax.set_xticks(x,names);ax.set_ylabel('OFF minus ON principal ($ billions)');ax.set_xlabel('Specification');ax.set_title('Conditional paired differences: Jun 2022–Nov 2025');ax.set_ylim(0,90);ax.legend(fontsize=9,loc='upper left')
    errors=[s['aggregate'][k]['weighted_rmse_monthly_pp'] for _,_,s,k in models]
    bx.bar(x,errors,color='#4477AA');bx.axhline(baseline['weighted_rmse_monthly_pp'],color='#333333',linestyle='--',label='Simple cohort-speed baseline')
    bx.axhline(models[0][2]['aggregate']['floor_psa_on']['weighted_rmse_monthly_pp'],color='#777777',linestyle=':',label='Legacy-selected 3.5% candidate')
    bx.set_xticks(x,names);bx.set_ylabel('Monthly-rate RMSE (percentage points)');bx.set_xlabel('Specification');bx.set_title('Retrospective ON fit: Jan 2024–Sep 2025');bx.set_ylim(0,.52);bx.legend(fontsize=9)
    fig.text(.5,.01,'Verified Freddie rerun: 75,000 simulation loans / 4,998 scored cohort-months.\nMixtures assume 75% sensitivity and the illustrative positive-gap response.',ha='center',fontsize=8)
    fig.tight_layout(rect=[0,.065,1,1],h_pad=2.2);fig.savefig(ROOT/'figures/fig14_corrected_comparison.pdf');fig.savefig(ROOT/'figures/fig14_corrected_comparison.png',dpi=350);plt.close(fig)
    write=dict(accepted_source_root=str(root),diagnostic_root=str(analysis),model_values=[dict(label=l,reported=p['reported_marginal_b'],cash=p['closed_pool_cash_marginal_b'],rmse=s['aggregate'][k]['weighted_rmse_monthly_pp']) for l,p,s,k in models],group_baseline_wins=wins,
        generated_sha256={str(p.relative_to(ROOT)):sha(p) for p in [final/'corrected_results.tex',final/'corrected_diagnostics.tex',ROOT/'figures/fig14_corrected_comparison.pdf',ROOT/'figures/fig14_corrected_comparison.png']})
    (analysis.parent/'publication_generated.json').write_text(json.dumps(write,indent=2)+'\n')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--analysis',required=True);a=p.parse_args();build(a.root,a.analysis)
