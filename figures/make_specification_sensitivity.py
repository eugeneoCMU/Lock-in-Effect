"""Current paired-assumption figure from precise artifacts; no transcribed points."""
from pathlib import Path
import json,hashlib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
def load_rows():
    names=['moving_share_bracket_offwindow_results.json','psa_level_sweep_results.json','floor_form_offwindow_results.json']
    data={n:json.loads((ROOT/'hazard/data'/n).read_text()) for n in names}
    assert data[names[0]]['parity_gates_all_pass'] and data[names[1]]['parity_gates_all_pass']
    rows=[{'label':'Moving share 0% (definitional)','value':0.,'source':names[0],'key':'null identity','group':'Moving share'}]
    for s in ['0.25','0.5','1']:
        rows.append({'label':f'Moving share {float(s)*100:g}%','value':data[names[0]]['cells'][s]['marginal_pp'],'source':names[0],'key':'cells.'+s,'group':'Moving share'})
    for s in [75,100,125,150]:
        key=f'4.991|{s}|6.5';rows.append({'label':f'{s} PSA baseline','value':data[names[1]]['cells'][key]['marginal_pp'],'source':names[1],'key':'cells.'+key,'group':'PSA speed'})
    r=next(r for r in data[names[2]]['rows'] if r['form']=='additive' and r['floor_annual_cpr_pct']==4.991)
    rows.append({'label':'Survival-combination form','value':r['band']['6.5']['marginal_pp'],'source':names[2],'key':'additive;4.991;6.5','group':'Turnover form'})
    return rows,{n:hashlib.sha256((ROOT/'hazard/data'/n).read_bytes()).hexdigest() for n in names}
def main():
    rows,hashes=load_rows();fig,ax=plt.subplots(figsize=(9.2,5.6),dpi=200)
    colors={'Moving share':'#27647a','PSA speed':'#ad5d33','Turnover form':'#5d657d'}
    yy=[0,1,2,3,4.5,5.5,6.5,7.5,9]
    for y,row in zip(yy,rows):
        v=row['value'];ax.scatter(v,y,s=70,color=colors[row['group']],zorder=3);ax.text(v+.25,y,f'{v:+.2f}',va='center',fontsize=11)
    ax.set_yticks(yy,[r['label'] for r in rows]);ax.invert_yaxis();ax.set_xlim(-.15,18.2);ax.set_xticks(range(0,17,2));ax.grid(axis='x',color='#dddddd');ax.set_axisbelow(True)
    ax.set_xlabel('Paired marginal (points of the $764.748 billion cap gap)',fontsize=10)
    ax.set_title('Separate assumptions, matched response-on/off pairs',fontsize=13,pad=15)
    for side in ['top','right','left']:ax.spines[side].set_visible(False)
    ax.tick_params(axis='y',length=0,pad=8);fig.tight_layout()
    fig.savefig(ROOT/'figures/fig13_specification_sensitivity.png',bbox_inches='tight');plt.close(fig)
    (ROOT/'figures/fig13_specification_sensitivity_provenance.json').write_text(json.dumps({'rows':rows,'artifact_sha256':hashes,'fixed':'saved sample; 4.991% floor; 100 PSA; full moving share; maximum form, except named variation'},indent=2)+'\n')
if __name__=='__main__':main()
