"""Artifact-bound scientific figures for the separate research supplement."""
from pathlib import Path
import argparse,json,hashlib
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def load(p):return json.loads(Path(p).read_text())
def build(output):
    output=Path(output);figs=output/'figures';figs.mkdir(exist_ok=True)
    calibration=output/'calibration-corrected-coverage';primary=load(calibration/'primary-results.json');expanding=load(calibration/'expanding-results.json')
    support=load(output/'support/attempt-002/support_grid.json');joint=load(output/'joint-sensitivity/results.json')
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    names=['additive','max','mixture:inherited_psa','mixture:matched_max_off','inherited_benchmark'];labels=['Selected additive','Selected max','Selected inherited mixture','Selected matched mixture','Inherited benchmark']
    fig,axes=plt.subplots(2,1,figsize=(7.8,7.4))
    for ax,d,title in zip(axes,[primary,expanding],['Train 2023; evaluate 2024–Sep 2025','Train 2023–24; evaluate Jan–Sep 2025']):
        ax.barh(np.arange(5),[d['aggregate'][n]['weighted_rmse_monthly_pp'] for n in names],color='#4477AA')
        ax.axvline(d['aggregate']['baseline']['weighted_rmse_monthly_pp'],color='#333333',linestyle='--',label='Training-fitted constant-speed baseline')
        ax.set_yticks(np.arange(5),labels);ax.invert_yaxis();ax.set_xlabel('Exposure-weighted monthly-rate RMSE (percentage points)');ax.set_title(title);ax.set_xlim(0,.15);ax.legend(loc='lower right',fontsize=8)
    fig.text(.5,.01,'Corrected Freddie conditional payoff predictions; identical support within each window. Previously examined outcomes.',ha='center',fontsize=8);fig.tight_layout(rect=[0,.05,1,1]);fig.savefig(figs/'calibration-errors.png',dpi=300);plt.close(fig)
    rows=support['cells'] if isinstance(support,dict) else support;years=[2018,2019,2023,2024,2025];ages=[12,24,36,60]
    selected={(r['year'],r['min_age_months']):r for r in rows if r['max_gap_bp']==-25}
    z=np.array([[selected[y,a]['end_cpr_pct'] if selected[y,a]['end_cpr_pct'] is not None else np.nan for a in ages] for y in years],float)
    fig,ax=plt.subplots(figsize=(7.5,5.2));im=ax.imshow(np.ma.masked_invalid(z),cmap='Blues',vmin=0,vmax=max(12,float(np.nanmax(z))))
    ax.set_xticks(range(4),['12','24','36','60']);ax.set_yticks(range(5),['2018','2019','2023','2024','2025 Jan–Sep']);ax.set_xlabel('Minimum cohort mean age (months)');ax.set_ylabel('Observation year');ax.set_title('Selected payoff-speed support: note minus market ≤−25bp')
    for i,y in enumerate(years):
        for j,a in enumerate(ages):
            r=selected[y,a];text='No support' if r['end_cpr_pct'] is None else f"{r['end_cpr_pct']:.2f}%\n{r['strata']} strata\n{r['months']} months"
            ax.text(j,i,text,ha='center',va='center',fontsize=8,color='white' if r['end_cpr_pct'] is not None and r['end_cpr_pct']>9 else 'black')
    fig.colorbar(im,ax=ax,label='Annualized end-exposure payoff-speed ratio (%)',shrink=.8)
    fig.text(.5,.01,'Corrected 2017–2021 Freddie cohorts; frozen within-month mean rates. Descriptive speed, not identified turnover.',ha='center',fontsize=8);fig.tight_layout(rect=[0,.05,1,1]);fig.savefig(figs/'floor-support.png',dpi=300);plt.close(fig)
    floors=sorted({r['floor_annual'] for r in joint['rows']});multipliers=sorted({r['response_multiplier'] for r in joint['rows']});v={(r['floor_annual'],r['response_multiplier']):r['reported_marginal_b'] for r in joint['rows']}
    fig,ax=plt.subplots(figsize=(7.5,4.7));data=np.array([[v[f,m] for m in multipliers] for f in floors]);im=ax.imshow(data,cmap='Blues')
    ax.set_xticks(range(3),[str(m)+'×' for m in multipliers]);ax.set_yticks(range(3),[f'{100*f:.3f}%' for f in floors]);ax.set_xlabel('Multiplier on imported response coefficient');ax.set_ylabel('Assumed annual hard-max floor (%)');ax.set_title('Exact floor/response scenarios: reported OFF minus ON principal')
    for i in range(3):
        for j in range(3):ax.text(j,i,f'${data[i,j]:.2f}B',ha='center',va='center',color='white' if data[i,j]>45 else 'black')
    fig.colorbar(im,ax=ax,label='Reported principal difference ($ billions)')
    fig.text(.5,.01,'June 2022–Nov 2025; fixed sample, 100 PSA, transitions and monthly holdings scaling. Finite scenario grid, not a CI.',ha='center',fontsize=8);fig.tight_layout(rect=[0,.05,1,1]);fig.savefig(figs/'joint-scenarios.png',dpi=300);plt.close(fig)
    (figs/'manifest.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in figs.glob('*.png')},indent=2)+'\n')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);build(p.parse_args().output)
