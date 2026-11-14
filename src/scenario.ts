/** Annual kWh and tCO2eq/MWh; scenarios never use model predictions. */
export function calculateScenario(baseKwh: number, rate: number, factor: number) {
  if (![baseKwh, rate, factor].every(Number.isFinite) || baseKwh < 0 || factor < 0 || rate < 0 || rate > 30) {
    throw new RangeError('Invalid scenario inputs');
  }
  const saving = baseKwh * rate / 100;
  return { saving, carbon: saving / 1000 * factor };
}

export function scenarioCsv(rows: (string | number)[][]) {
  return '\uFEFF' + rows.map(row => row.map(value => `"${String(value).replaceAll('"', '""')}"`).join(',')).join('\r\n') + '\r\n';
}
