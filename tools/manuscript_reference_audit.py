"""Expand active TeX inputs and detect semantically wrong reference object types."""
from pathlib import Path
import re,sys,json

def expand_source(path,seen=None):
    path=Path(path).resolve();seen=set() if seen is None else set(seen)
    if path in seen:raise ValueError(f'Cyclic input: {path}')
    seen.add(path);s=path.read_text()
    s=re.sub(r'(?<!\\)%[^\n]*','',s)
    # Preserved historical editions may have inactive blocks; never audit them as live.
    while r'\iffalse' in s:
        a=s.index(r'\iffalse');depth=1;end=None
        for m in re.finditer(r'\\(?:if\w*|fi)\b',s[a+8:]):
            depth+=-1 if m.group()==r'\fi' else 1
            if depth==0:end=a+8+m.end();break
        if end is None:raise ValueError('Unclosed conditional')
        s=s[:a]+s[end:]
    def load(m):
        child=path.parent/m.group(1)
        if not child.suffix:child=child.with_suffix('.tex')
        return expand_source(child,seen)
    return re.sub(r'\\input\{([^}]+)\}',load,s)

def semantic_errors(source):
    s=re.sub(r'(?<!\\)%[^\n]*','',source);stack=[];section=None;labels={};errors=[]
    token=r'\\(begin|end)\{([^}]+)\}|\\(section|subsection|subsubsection)\b|\\label\{([^}]+)\}'
    for m in re.finditer(token,s):
        kind,env,sec,label=m.groups()
        if kind=='begin':stack.append(env)
        elif kind=='end':
            if stack and stack[-1]==env:stack.pop()
        elif sec:section=sec
        else:
            typ=next((e for e in reversed(stack) if e in ['equation','align','gather','table','longtable','figure']),section)
            if label in labels:errors.append('Duplicate label '+label)
            labels[label]=typ
            prefix=label.split(':')[0];valid={'eq':{'equation','align','gather'},'tab':{'table','longtable'},'fig':{'figure'},'sec':{'section','subsection','subsubsection'},'app':{'section','subsection'}}
            if prefix in valid and typ not in valid[prefix]:errors.append(f'{label} attached to {typ}')
    for kind,label in re.findall(r'\\(eqref|ref|autoref|pageref)\{([^}]+)\}',s):
        if label not in labels:errors.append('Missing label '+label)
        elif kind=='eqref' and labels[label] not in {'equation','align','gather'}:errors.append('Equation reference targets '+str(labels[label])+': '+label)
    return errors

def main():
    root=Path(__file__).resolve().parents[1];report={}
    for name in ['paper_final_v1','paper_final_v1_long_abstract']:
        p=root/'paper/final'/f'{name}.tex';s=expand_source(p);errs=semantic_errors(s)
        report[name]={'errors':errs,'labels':len(re.findall(r'\\label\{',s)),'references':len(re.findall(r'\\(?:eqref|ref)\{',s))}
    print(json.dumps(report,indent=2));return int(any(r['errors'] for r in report.values()))
if __name__=='__main__':sys.exit(main())
