"""Generate a source-bound research supplement from accepted separate experiments.

Run with bundled Python (reportlab); figures are generated separately with the
scientific Python runtime. No source data, model state or accepted paper edits.
"""
from pathlib import Path
import argparse,json,hashlib,html,re
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,Image,PageBreak
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import letter

LABELS={'baseline':'Cohort-speed baseline','max':'Selected hard maximum','additive':'Selected additive','mixture:inherited_psa':'Selected inherited mixture','mixture:matched_max_off':'Selected matched mixture','inherited_benchmark':'Inherited hard-max benchmark'}
def load(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def seal(root,file='completed.json'):
 d=load(root/file)
 for n,h in d.get('output_sha256',{}).items():
  if sha(root/n)!=h:raise ValueError('Stale output '+str(root/n))
 return d

def build(root):
 root=Path(root);cal=root/'calibration-corrected-coverage';support=root/'support/attempt-002';dynamic=root/'dynamic-refinancing/attempt-20261014T152157935190Z';joint=root/'joint-sensitivity'
 for p in (cal,support,joint):seal(p)
 dm=load(dynamic/'manifest.json')
 # Dynamic worker manifest has its own input/output contract.
 outputs=dm.get('output_sha256',dm.get('outputs_sha256',{}))
 for n,h in outputs.items():
  p=Path(n);p=p if p.is_absolute() else dynamic/p
  if sha(p)!=h:raise ValueError('Dynamic output changed')
 datasets={n:load(cal/(n+'-results.json')) for n in ['primary','expanding']}
 support_grid=load(support/'support_grid.json');mature=load(support/'mature2019_measurement_inference.json');envelope=load(support/'structural_envelope.json');ds=load(dynamic/'results.json');js=load(joint/'results.json')
 log=(root/'regression-final.log').read_text();m=re.search(r'(\d+) passed, (\d+) skipped',log)
 if not m:raise ValueError('Final integrated suite receipt missing')
 testcount=int(m[1]);styles=getSampleStyleSheet();styles.add(ParagraphStyle(name='SmallBody',parent=styles['BodyText'],fontSize=8.5,leading=11,spaceAfter=7));styles.add(ParagraphStyle(name='Cell',fontName='Helvetica',fontSize=8.5,leading=10.5));styles.add(ParagraphStyle(name='MonoSmall',fontName='Courier',fontSize=8.2,leading=11,spaceAfter=8))
 styles['BodyText'].fontSize=10;styles['BodyText'].leading=14;styles['BodyText'].spaceAfter=9
 story=[]
 def text(s,style='BodyText'):
  s=s.replace('months0,12and24','months 0, 12 and 24').replace('with0.5x,1xand1.5x','with 0.5x, 1x and 1.5x')
  parts=re.split(r'(<[^>]+>)',s)
  for i in range(0,len(parts),2):
   parts[i]=re.sub(r'(?<=[A-Za-z])(?=[0-9])',' ',parts[i]);parts[i]=re.sub(r'(?<=[0-9])(?=[A-Za-z])',' ',parts[i])
  story.append(Paragraph(''.join(parts),styles[style]))
 def heading(s):text(s,'Heading1')
 def table(headers,rows,widths):
  data=[[Paragraph(html.escape(str(c)),styles['Cell']) for c in row] for row in [headers]+rows]
  t=Table(data,colWidths=widths,repeatRows=1,hAlign='LEFT');t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e6e9ed')),('LINEBELOW',(0,0),(-1,0),.8,colors.HexColor('#333333')),('LINEBELOW',(0,-1),(-1,-1),.5,colors.HexColor('#777777')),('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]));story.append(t);story.append(Spacer(1,10))
 def image(name,width,height):story.append(Image(str(root/'figures'/name),width=width,height=height));story.append(Spacer(1,8))
 heading('Corrected-data research follow-through')
 text('October 14, 2026. Separate calibration, dynamic refinancing, seasoning-support and assumption-sensitivity experiments. The accepted paper and its inherited-parameter <b>$16.2155 billion</b> reported benchmark remain unchanged.')
 text('<b>Main finding:</b> training-selected structural candidates improve on the inherited benchmark, but the training-fitted cohort-speed baseline still has lower evaluation RMSE in both chronological windows. This work does not establish an empirically preferred runoff estimate.')
 heading('1. Chronological calibration')
 text('Primary window: train January-December 2023; evaluate January 2024-September 2025. Expanding window: train January 2023-December 2024; evaluate January-September 2025. Each selection receipt is sealed before its evaluation-payoff reader runs. All outcomes were previously examined; this is retrospective validation.')
 rows=[]
 for name,d in datasets.items():
  for model in ['baseline','overall','inherited_benchmark']:
   a=d['aggregate'][model];rows.append([name,'Selected overall mixture' if model=='overall' else LABELS[model],f"{a['weighted_rmse_monthly_pp']:.5f}",f"{a['weighted_mae_monthly_pp']:.5f}",f"{a['predicted_b']:.2f}"])
 table(['Window','Specification','RMSE (pp)','MAE (pp)','Predicted ($B)'],rows,[64,182,83,83,104])
 text('RMSE/MAE are exposure-weighted monthly payoff-rate errors in percentage points. Dollar totals are conditional voluntary-payoff predictions, not paired runoff effects. Primary observed payoff is $'+f"{datasets['primary']['aggregate']['baseline']['observed_b']:.4f}"+'B; expanding observed payoff is $'+f"{datasets['expanding']['aggregate']['baseline']['observed_b']:.4f}"+'B. All models share the same scoring support within each window.','SmallBody')
 text('The 112-candidate grid varies PSA, floor, mixture reference and assumed responsive share under two fixed response conversions. Training selects minimum exposure-weighted RMSE with a deterministic candidate-ID tie break. Both overall selections use matched-OFF mixture, share 1, PSA 100 and the legacy response conversion. This is predictive selection, not a measured sale share or causal elasticity.','SmallBody')
 text(f"Primary support: {datasets['primary']['support']['retained_rows']:,} scored cohort-months in {datasets['primary']['support']['retained_cells']} cells. Expanding support: {datasets['expanding']['support']['retained_rows']:,} rows in {datasets['expanding']['support']['retained_cells']} cells. Forecasts advance full monthly latent calendars from the immediately preceding month; observed evaluation burnout and payoffs never update them.",'SmallBody')
 text('The exact May2022 sample covariates and advancing pre-period cohort mean ages remain approximations. Scores condition on realized opening exposure and mortgage rates. This exercise does not validate a forward balance forecast, modified current contract terms, causal imported response, cause-specific hazards, or full-SOMA transport.','SmallBody')
 story.append(PageBreak());heading('Prediction comparison on identical support')
 image('calibration-errors.png',510,484)
 text('Selected means selected on the corresponding training window, never on displayed evaluation errors. The baseline is a training-fitted cell-specific constant payoff speed. The dashed comparator beats all displayed structural candidates. Source: calibration-corrected-coverage parameter freezes, scored rows and results.','SmallBody')
 story.append(PageBreak());heading('2. Seasoning support and denominator audit')
 image('floor-support.png',510,354)
 text('The full grid covers five years, four cohort-mean-age thresholds and five rate gaps: 100 cells, 71 supported and 29 without end-exposure support. Ages are observed cohort means, not every borrower\'s age. Later-year windows end September2025; no unsupported age cell is imputed.','SmallBody')
 text('The designated mature diagnostic (2019, mean age at least24months, note minus market at most -25bp) has <b>32 cohort-months, nine strata, eight calendar months and3,154 loan-count months</b>. It fails the prespecified ten-stratum inference guard. No mature-floor confidence interval is produced.')
 text('Its descriptive annualized end-exposure speed is <b>8.14461%</b>; the separately matched adjacent-opening speed is <b>8.43365%</b>. The latter uses adjacent loan-level opening exposure and excludes first-observed/gap payoff dollars from the numerator. Those are distinct denominator conventions. Neither identifies an involuntary turnover hazard or validates transporting a floor across periods.','SmallBody')
 text('Frozen weekly within-month mean mortgage rates determine the support grid. The existing primary2018 floor measurement and its conditional interval remain preserved; this grid does not replace them. Full counts, missing months and matched numerators appear in support_grid.csv.','SmallBody')
 story.append(PageBreak());heading('3. Dynamic refinancing scenario')
 text('Monthly borrower state: principal, contract coupon, remaining term and supplied market-rate state. Keep or refinance to today\'s supplied quote before the next payment. Refinancing preserves principal and remaining term, pays a proportional cash cost immediately, and retains future exercise opportunities. Equal branches wait. The solver runs to contractual maturity, clears the final balance, and has no production hook.')
 text('With payment fraction a(c,n), residual fraction z(c,n), discount d and supplied Markov matrix P, the normalized borrower-cost recursion is:')
 text('hold[n,c,x] = d * (a(c,n) + z(c,n) * E[v[n-1,c,x\']])<br/>exercise[n,c,x] = cost_fraction + hold[n,quote(x),x]<br/>v = lower-cost branch; ties wait. J(balance,c,n,x) = balance * v.','MonoSmall')
 text('These are proposed project equations. Proportional costs give exact balance homogeneity, so no balance grid is needed. Fixed-dollar or financed costs, sale/default, taxes, qualification, inattention and endogenous lender pricing are absent. The finite supplied rate chain is solved directly; quote rounding sensitivity is not convergence to an estimated continuous process.','SmallBody')
 rows=[]
 for s in ds['scenarios']:
  if s['group']=='base':rows.append([s['id'].replace('_',' '),f"${s['expected_cost_usd']:,.2f}",str([x['month'] for x in s['exercises']]),f"${s['total_cash_refinancing_cost']:,.2f}"])
 table(['Supplied scenario','Borrower cash PV','Exercise months','Cash fees'],rows,[188,112,104,112])
 text('All base scenarios start with $200,000 principal,120 remaining months and4% annual nominal discount. In the falling-rate scenario, static refinancing today saves $19,360.67, yet the dynamic optimum waits one month. The repeated-opportunity scenario refinances at months0,12and24 and pays each fee separately. These are conditional demonstrations, not observed exercise frequencies.','SmallBody')
 text('Source scope: the <a href="https://onlinelibrary.wiley.com/doi/10.1111/j.1540-6229.2005.00132.x" color="#225588">Dunn-Spatt publisher abstract</a> motivates future refinancing costs; its full text remains unavailable. Separate <a href="https://laibson.scholars.harvard.edu/sites/g/files/omnuum5971/files/laibson/files/optimal_mortgage_refinancing_092012.pdf" color="#225588">Agarwal-Driscoll-Laibson primary full text</a> supports recursive exercise logic. This solver replicates neither paper\'s equilibrium.','SmallBody')
 story.append(PageBreak());heading('4. Broader assumption sensitivity')
 image('joint-scenarios.png',510,320)
 text(f"Nine exact hard-max pairs cross the corrected floor measurement's lower endpoint,point and upper endpoint with0.5x,1xand1.5x the imported beta. The actual engine decline conversion is inverted to exercise those coefficients; OFF paths are identical within each floor and principal identities reconcile. Reported differences span <b>${js['reported_envelope_b'][0]:.2f}-${js['reported_envelope_b'][1]:.2f}B</b>; closed-pool cash spans <b>${js['cash_envelope_b'][0]:.2f}-${js['cash_envelope_b'][1]:.2f}B</b>.")
 text(f"The separate accepted40-mixture matrix spans <b>${envelope['reported_marginal_b']['min']:.4f}-${envelope['reported_marginal_b']['max']:.4f}B</b> reported and <b>${envelope['closed_pool_cash_marginal_b']['min']:.4f}-${envelope['closed_pool_cash_marginal_b']['max']:.4f}B</b> in pool cash. Its axes are reference schedule, response conversion, gap treatment and assumed sensitive share. The slightly negative minimum belongs to zero-share refinancing-preserving mode, which still enables favorable-gap boosting; positive-only zero-share cases satisfy identity.",'SmallBody')
 text('<b>These are finite structural envelopes, not confidence intervals.</b> No joint probability model for response, share, reference, seasoning and transport is identified. Combining extrema does not supply total statistical coverage. Reported principal uses leg-specific monthly holdings scaling; closed-pool cash is unscaled principal cash.','SmallBody')
 story.append(PageBreak());heading('5. Sale/refinance evidence and remaining empirical work')
 text('The <a href="https://www.freddiemac.com/fmac-resources/research/pdf/user_guide.pdf" color="#225588">official Freddie SFLLD guide</a> defines ordinary code01 as prepaid or matured voluntary payoff. Origination purpose describes the new loan at origination and cannot classify its later payoff. Third-party/short/whole-loan sale codes describe different termination objects; they are not general homeowner-sale labels. A Relief Refinance predecessor link identifies only that restricted program. Missing linkage is not positive evidence of sale.')
 text('The audit found no verified general sale/refinance label or common external identifier for this public Freddie population. Linking deeds, releases and new liens would need historical access, a reliable linkage, a comparable outstanding-loan denominator and validation. <a href="https://ffiec.cfpb.gov/documentation/publications/loan-level-datasets/lar-data-fields/" color="#225588">Public HMDA origination purpose</a> and <a href="https://www.fhfa.gov/data/nsmo" color="#225588">FHFA NSMO motivations</a> can inform separate scenarios but do not silently label these payoff events. No data was purchased and no provider was contacted.')
 text('Consequently, the dynamic model remains a tested scenario. It is not inserted into the production four-intensity model or used to replace the accepted runoff dollars. The empirical sale/refinance decomposition, cost distribution, future-rate expectations, seasoning transport and representative SOMA mapping remain unestimated. Full Dunn-Spatt access and these data inputs are needed for a closer structural replication or empirical calibration.')
 heading('Verification and preservation')
 text(f"Final integrated regression: <b>{testcount:,} passed, one skipped</b>. Meaningful tests include future-outcome selection invariance, first-month calendar refusal, requested-window exclusion counts, parity with accepted forecasts, brute-force borrower action trees, repeated fee accounting, transition validation, sparse-support inference refusal, accepted matrix completeness, and actual floor/beta engine changes.")
 text('The independent review found two calibration interface/reporting issues: inherited exclusion dates and a missing-first-month calendar guard. Both were corrected with failing-then-passing tests; the first sealed calibration is preserved and superseded only for coverage/guard reporting. Corrected calibration forecasts and scores reproduce its original results. All nine exact sensitivity pairs and retained source receipts are sealed after before/after hash checks. Accepted paper/source snapshots remain unchanged.','SmallBody')
 text('Reproducibility: parameter freezes, full training scores, common-support scored rows, latent predictions,100-cell support grid,40-scenario envelope, dynamic policies/traces and exact paired monthly accounting are saved beside this supplement. Raw loan data and credentials are excluded from the delivered package. Source acquisition remains under its original access terms.','SmallBody')
 def footer(c,doc):
  c.setFont('Helvetica',8);c.setFillColor(colors.HexColor('#666666'));c.drawString(48,27,'October 14, 2026 | Conditional research experiments');c.drawRightString(564,27,str(doc.page))
 pdf=root/'research-supplement.pdf';doc=SimpleDocTemplate(str(pdf),pagesize=letter,leftMargin=48,rightMargin=48,topMargin=42,bottomMargin=43,title='Corrected-data research follow-through',author='Eugene Ong');doc.build(story,onFirstPage=footer,onLaterPages=footer)
 summary=dict(calibration={n:dict(aggregate=d['aggregate'],support=d['support'],selected=d['parameters']) for n,d in datasets.items()},mature2019=mature,structural_envelope=envelope,joint=js,dynamic=ds,tests_passed=testcount,pdf_sha256=sha(pdf),status='separate_research_experiments_completed; causal identification and unavailable full text remain unresolved')
 (root/'research_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',required=True);build(p.parse_args().output)
