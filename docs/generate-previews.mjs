/** Static SVG snapshots from the same package-to-diagram model used by the viewer. */
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {buildDiagram} from './model.js';
import {renderSvg} from './diagram-svg.js';
const here = path.dirname(fileURLToPath(import.meta.url));
const output = path.join(here,'previews');
fs.mkdirSync(output,{recursive:true});
const catalog = JSON.parse(fs.readFileSync(path.join(here,'examples.json'),'utf8'));
const targets = new Set(catalog.map(entry => path.basename(entry.file, '.json') + '.svg'));
for (const file of fs.readdirSync(output)) {
  if (file.endsWith('.svg') && !targets.has(file)) fs.unlinkSync(path.join(output,file));
}
for (const entry of catalog) {
  const pkg = JSON.parse(fs.readFileSync(path.join(here,entry.file),'utf8'));
  const target = path.basename(entry.file,'.json') + '.svg';
  fs.writeFileSync(path.join(output,target),renderSvg(buildDiagram(pkg),true));
  console.log(target);
}
