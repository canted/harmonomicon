import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {CATALOG_VERSION, FORMAT} from './formats.js';
const here = path.dirname(fileURLToPath(import.meta.url));
const source = path.join(here, `../format/${CATALOG_VERSION}/examples`);
const target = path.join(here, 'examples');
fs.mkdirSync(target, {recursive:true});
const files = fs.readdirSync(source).filter(name => name.endsWith('.json')).sort();
for (const file of fs.readdirSync(target)) {
  if (file.endsWith('.json') && !files.includes(file)) fs.unlinkSync(path.join(target, file));
}
const catalog = files.map(file => {
  const bytes = fs.readFileSync(path.join(source, file));
  const pkg = JSON.parse(bytes);
  if (pkg.format !== FORMAT) throw new Error(`Unexpected format in ${file}: ${pkg.format}`);
  fs.writeFileSync(path.join(target, file), bytes);
  return {file:`examples/${file}`, title:pkg.content.title, id:pkg.id, format:pkg.format};
});
for (const entry of catalog) {
  // Package identity distinguishes same-title variants without changing their JSON.
  const slug = entry.id.split('.').pop();
  const titlePrefix = entry.title.toLowerCase().replace(/[^a-z0-9]+/g,'-')+'-';
  const variant = (slug.startsWith(titlePrefix) ? slug.slice(titlePrefix.length) : slug).replaceAll('-',' ');
  entry.label = catalog.filter(other => other.title === entry.title).length > 1
    ? `${variant.charAt(0).toUpperCase()+variant.slice(1)} · ${entry.title}` : entry.title;
}
fs.writeFileSync(path.join(here, 'examples.json'), JSON.stringify(catalog, null, 2) + '\n');
console.log(`Synced ${catalog.length} packages from format/${CATALOG_VERSION}/examples.`);
