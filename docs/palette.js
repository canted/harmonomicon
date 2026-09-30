// RGB pairs transcribed from the supplied SVG.
export const palette = Object.freeze({
  pink: '#db4275', pinkDark: '#5e122b',
  yellow: '#dbbd42', yellowDark: '#6d5603',
  green: '#6eb951', greenDark: '#2b561b',
  cyan: '#3aa8be', cyanDark: '#213d45',
  blue: '#2c7fd8', blueDark: '#153c66',
  purple: '#6652b1', purpleDark: '#291d53',
  white: '#ffffff'
});

/** Colors depend only on declared nesting and sequence position. */
export function diagramFill(node) {
  const stages = [palette.blue, palette.cyan, palette.yellow, palette.green, palette.purple, palette.pink];
  return stages[node.column % stages.length];
}
