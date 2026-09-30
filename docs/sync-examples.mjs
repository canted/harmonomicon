import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const here=path.dirname(fileURLToPath(import.meta.url));
for(const name of ['group-check-in','image-caption-vote']){
  fs.copyFileSync(path.join(here,'../format/0.12/examples',`${name}.json`),path.join(here,'examples',`${name}.json`));
  console.log(`${name}.json`);
}
