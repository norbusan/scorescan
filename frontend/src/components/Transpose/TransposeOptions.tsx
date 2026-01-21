import React, { useState } from 'react';
import { Music, ArrowRight } from 'lucide-react';
import { MUSICAL_KEYS } from '../../types';

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

  const updateOptions = (updates: Partial<TransposeSettings>) => {
    const newSettings = {
      enabled: updates.enabled ?? enabled,
      mode: updates.mode ?? mode,
      semitones: updates.semitones ?? semitones,
      fromKey: updates.fromKey ?? fromKey,
      toKey: updates.toKey ?? toKey,
    };
    
    if (updates.enabled !== undefined) setEnabled(updates.enabled);
    if (updates.mode !== undefined) setMode(updates.mode);
    if (updates.semitones !== undefined) setSemitones(updates.semitones);
    if (updates.fromKey !== undefined) setFromKey(updates.fromKey);
    if (updates.toKey !== undefined) setToKey(updates.toKey);
    
    onOptionsChange(newSettings);
  };

  const formatSemitones = (n: number) => {
    if (n === 0) return '0 (no change)';
    return n > 0 ? `+${n}` : `${n}`;
  };

  return (
    <div className="card p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <Music className="h-5 w-5 text-primary-600" />
          <h3 className="font-medium text-gray-900">Transpose</h3>
        </div>
        <label className="relative inline-flex items-center cursor-pointer">
          <input
            type="checkbox"
            checked={enabled}
            onChange={(e) => updateOptions({ enabled: e.target.checked })}
            className="sr-only peer"
          />
          <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
        </label>
      </div>

      {enabled && (
        <div className="space-y-4">
          {/* Mode selector */}
          <div className="flex rounded-lg bg-gray-100 p-1">
            <button
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
