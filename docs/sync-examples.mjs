import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const here = path.dirname(fileURLToPath(import.meta.url));
const source = path.join(here, '../format/0.16/examples');
const target = path.join(here, 'examples');
fs.mkdirSync(target, {recursive:true});
const files = fs.readdirSync(source).filter(name => name.endsWith('.json')).sort();
for (const file of fs.readdirSync(target)) {
  if (file.endsWith('.json') && !files.includes(file)) fs.unlinkSync(path.join(target, file));
}
const catalog = files.map(file => {
  const bytes = fs.readFileSync(path.join(source, file));
  const pkg = JSON.parse(bytes);
  fs.writeFileSync(path.join(target, file), bytes);
  return {file:`examples/${file}`, title:pkg.content.title};
});
fs.writeFileSync(path.join(here, 'examples.json'), JSON.stringify(catalog, null, 2) + '\n');
console.log(`Synced ${catalog.length} packages from format/0.16/examples.`);
