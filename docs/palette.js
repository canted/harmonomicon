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

/** Mix with white in sRGB; purple needs 15% to meet 4.5:1 against black. */
export function lighten(hex, amount = 0.10) {
  return '#' + hex.slice(1).match(/../g).map(channel =>
    Math.round(parseInt(channel,16)*(1-amount)+255*amount).toString(16).padStart(2,'0')).join('');
}

/** Colors depend only on declared nesting and sequence position. */
export function diagramFill(node) {
  const stages = [palette.blue, palette.cyan, palette.yellow, palette.green, palette.purple, palette.pink];
  const color = stages[node.column % stages.length];
  return lighten(color, color === palette.purple ? 0.15 : 0.10);
}
