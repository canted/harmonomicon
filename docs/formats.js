/** Catalog version and structural inspection support, not runtime support. */
export const CATALOG_VERSION = '0.24';
export const SUPPORTED_VERSIONS = ['0.20', '0.21', '0.22', '0.23', '0.24'];
export const FORMAT = `harmonomicon.activity-package/${CATALOG_VERSION}`;
export function formatInfo(format) {
  const version = SUPPORTED_VERSIONS.find(value => format === `harmonomicon.activity-package/${value}`);
  if (!version) throw new Error(`This viewer supports package formats ${SUPPORTED_VERSIONS.join(', ')}.`);
  const base = `https://github.com/canted/harmonomicon/blob/main/format/${version}`;
  return {version, specification:`${base}/operations.md`, schema:`${base}/package.schema.json`};
}
