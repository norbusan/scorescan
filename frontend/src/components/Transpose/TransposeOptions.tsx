import React, { useState } from 'react';
import { Music, ArrowRight } from 'lucide-react';

interface TransposeOptionsProps {
  onOptionsChange: (options: TransposeSettings) => void;
}

export interface TransposeSettings {
  enabled: boolean;
  mode: 'semitones' | 'keys';
  semitones: number;
  fromKey: string;
  toKey: string;
}

const MAJOR_KEYS = ['C', 'C#', 'Db', 'D', 'Eb', 'E', 'F', 'F#', 'Gb', 'G', 'Ab', 'A', 'Bb', 'B'];
const MINOR_KEYS = ['Cm', 'C#m', 'Dm', 'Ebm', 'Em', 'Fm', 'F#m', 'Gm', 'Abm', 'Am', 'Bbm', 'Bm'];

export default function TransposeOptions({ onOptionsChange }: TransposeOptionsProps) {
  const [enabled, setEnabled] = useState(false);
  const [mode, setMode] = useState<'semitones' | 'keys'>('semitones');
  const [semitones, setSemitones] = useState(0);
  const [fromKey, setFromKey] = useState('C');
  const [toKey, setToKey] = useState('C');

  const handleToggle = () => {
    const newEnabled = !enabled;
    setEnabled(newEnabled);
    onOptionsChange({
      enabled: newEnabled,
      mode,
      semitones,
      fromKey,
      toKey,
    });
  };

  const updateOptions = (updates: Partial<TransposeSettings>) => {
    const newMode = updates.mode ?? mode;
    const newSemitones = updates.semitones ?? semitones;
    const newFromKey = updates.fromKey ?? fromKey;
    const newToKey = updates.toKey ?? toKey;
    
    if (updates.mode !== undefined) setMode(updates.mode);
    if (updates.semitones !== undefined) setSemitones(updates.semitones);
    if (updates.fromKey !== undefined) setFromKey(updates.fromKey);
    if (updates.toKey !== undefined) setToKey(updates.toKey);
    
    onOptionsChange({
      enabled,
      mode: newMode,
      semitones: newSemitones,
      fromKey: newFromKey,
      toKey: newToKey,
    });
  };

  const formatSemitones = (n: number) => {
    if (n === 0) return '0 (no change)';
    return n > 0 ? `+${n}` : `${n}`;
  };

  return (
    <div className="border border-gray-200 rounded-lg p-4 bg-gray-50">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <Music className="h-5 w-5 text-primary-600" />
          <h3 className="font-medium text-gray-900">Transpose</h3>
        </div>
        <button
          type="button"
          role="switch"
          aria-checked={enabled}
          onClick={handleToggle}
          className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 ${
            enabled ? 'bg-primary-600' : 'bg-gray-200'
          }`}
        >
          <span
            className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
              enabled ? 'translate-x-6' : 'translate-x-1'
            }`}
          />
        </button>
      </div>

      {enabled && (
        <div className="space-y-4">
          {/* Mode selector */}
          <div className="flex rounded-lg bg-gray-200 p-1">
            <button
              type="button"
              onClick={() => updateOptions({ mode: 'semitones' })}
              className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors ${
                mode === 'semitones'
                  ? 'bg-white text-gray-900 shadow'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              By Semitones
            </button>
            <button
              type="button"
              onClick={() => updateOptions({ mode: 'keys' })}
              className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors ${
                mode === 'keys'
                  ? 'bg-white text-gray-900 shadow'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              By Key
            </button>
          </div>

          {mode === 'semitones' ? (
            <div>
              <label className="block text-sm text-gray-600 mb-2">
                Semitones: <span className="font-medium text-gray-900">{formatSemitones(semitones)}</span>
              </label>
              <input
                type="range"
                min="-12"
                max="12"
                value={semitones}
                onChange={(e) => updateOptions({ semitones: parseInt(e.target.value) })}
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-primary-600"
              />
              <div className="flex justify-between text-xs text-gray-400 mt-1">
                <span>-12</span>
                <span>0</span>
                <span>+12</span>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              <div>
                <label className="block text-sm text-gray-600 mb-2">From Key</label>
                <select
                  value={fromKey}
                  onChange={(e) => updateOptions({ fromKey: e.target.value })}
                  className="input"
                >
                  <optgroup label="Major Keys">
                    {MAJOR_KEYS.map((key) => (
                      <option key={key} value={key}>{key} Major</option>
                    ))}
                  </optgroup>
                  <optgroup label="Minor Keys">
                    {MINOR_KEYS.map((key) => (
                      <option key={key} value={key}>{key.replace('m', '')} Minor</option>
                    ))}
                  </optgroup>
                </select>
              </div>

              <div className="flex justify-center">
                <ArrowRight className="h-5 w-5 text-gray-400" />
              </div>

              <div>
                <label className="block text-sm text-gray-600 mb-2">To Key</label>
                <select
                  value={toKey}
                  onChange={(e) => updateOptions({ toKey: e.target.value })}
                  className="input"
                >
                  <optgroup label="Major Keys">
                    {MAJOR_KEYS.map((key) => (
                      <option key={key} value={key}>{key} Major</option>
                    ))}
                  </optgroup>
                  <optgroup label="Minor Keys">
                    {MINOR_KEYS.map((key) => (
                      <option key={key} value={key}>{key.replace('m', '')} Minor</option>
                    ))}
                  </optgroup>
                </select>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
