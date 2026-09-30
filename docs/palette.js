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

export function tint(hex, colorPart = 0.1) {
  const channels = [1, 3, 5].map(index => Number.parseInt(hex.slice(index, index + 2), 16));
  return '#' + channels.map(channel => Math.round(channel * colorPart + 255 * (1 - colorPart)).toString(16).padStart(2, '0')).join('');
}
