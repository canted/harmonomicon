/** Static SVG snapshots from the same package-to-diagram model used by the viewer. */
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {buildDiagram} from './model.js';
const here=path.dirname(fileURLToPath(import.meta.url));
const output=path.join(here,'previews');
fs.mkdirSync(output,{recursive:true});
const escape=value=>String(value).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'",'&apos;');
function wrap(s,max=22){
  const words=s.split(/\s+/), lines=[''];
  for(const word of words){
    const i=lines.length-1;
    if((lines[i]+' '+word).trim().length>max && lines[i])lines.push(word);
    else lines[i]=(lines[i]+' '+word).trim();
  }
  return lines.slice(0,2);
}
function render(diagram){
  const nodeW=174,nodeH=70,step=300;
  const x=n=>80+n.column*step,y=n=>130+n.row*155;
  const maxCol=Math.max(...diagram.nodes.map(n=>n.column));
  const hasBranch=diagram.nodes.some(n=>n.row>0);
  const width=x({column:maxCol})+nodeW+80,height=hasBranch?410:270;
  const byId=new Map(diagram.nodes.map(n=>[n.id,n]));
  const edges=diagram.edges.map(e=>{
    const a=byId.get(e.source),b=byId.get(e.target);
    let d,lx,ly;
    if(a===b){const sx=x(a)+nodeW-35,sy=y(a);d=`M ${sx} ${sy} C ${sx+10} ${sy-80}, ${sx-95} ${sy-80}, ${sx-85} ${sy}`;lx=sx-37;ly=sy-62;}
    else{const sx=x(a)+nodeW,sy=y(a)+nodeH/2,tx=x(b)-9,ty=y(b)+nodeH/2;d=`M ${sx} ${sy} C ${sx+37} ${sy}, ${tx-37} ${ty}, ${tx} ${ty}`;lx=(sx+tx)/2;ly=a.row===b.row ? sy-54 : (sy+ty)/2-13;}
    const labelLines=e.label.split(' · '); const label=labelLines.map((line,i)=>`<text x="${lx}" y="${ly+i*13}" text-anchor="middle" fill="#526079" font-size="10" font-family="Arial,sans-serif">${escape(line)}</text>`).join(''); return `<path d="${d}" fill="none" stroke="#8295b5" stroke-width="2" marker-end="url(#arrow)"/>${label}`;
  }).join('');
  const nodes=diagram.nodes.map(n=>{
    const terminal=['complete','closed'].includes(n.id),branch=['insufficient','stalled'].includes(n.id);
    const stroke=branch?'#ad6e41':terminal?'#6842b9':'#285bd2';
    const fill=branch?'#fff3e8':terminal?'#f5f0ff':'#edf4ff';
    const lines=wrap(n.title);
    const text=lines.map((line,i)=>`<text x="${x(n)+nodeW/2}" y="${y(n)+(lines.length===1?37:27)+i*17}" text-anchor="middle" fill="#172238" font-family="Arial,sans-serif" font-size="13" font-weight="700">${escape(line)}</text>`).join('');
    return `<rect x="${x(n)}" y="${y(n)}" width="${nodeW}" height="${nodeH}" fill="${fill}" stroke="${stroke}" stroke-width="3"/>${text}`;
  }).join('');
  return `<svg xmlns="http://www.w3.org/2000/svg" role="img" aria-label="${escape(diagram.title)} package flow" viewBox="0 0 ${width} ${height}" width="${width}" height="${height}">
<defs><marker id="arrow" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto"><path d="M0 0L7 3.5L0 7" fill="#8295b5"/></marker></defs>
<rect width="100%" height="100%" fill="#fff"/><text x="80" y="51" fill="#172238" font-family="Arial,sans-serif" font-size="24" font-weight="700">${escape(diagram.title)}</text><text x="80" y="77" fill="#6842b9" font-family="monospace" font-size="12">behavior: ${escape(diagram.contract)}</text>
${edges}${nodes}<text x="80" y="${height-26}" fill="#536078" font-family="Arial,sans-serif" font-size="11">Package blueprint · times and participants are supplied when an instance starts</text></svg>\n`;
}
for(const [name,target] of [['group-check-in','check-in.svg'],['image-caption-vote','caption-contest.svg']]){
  const pkg=JSON.parse(fs.readFileSync(path.join(here,'examples',`${name}.json`),'utf8'));
  fs.writeFileSync(path.join(output,target),render(buildDiagram(pkg)));
  console.log(target);
}
