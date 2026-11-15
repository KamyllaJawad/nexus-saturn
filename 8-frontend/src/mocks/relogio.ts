// Dados mockados do relógio, para a prévia dos três estados.

import type { NivelSaude } from './tripulacao'

export interface EstadoRelogio {
  fc: number 
  spo2: number 
  homeostase: number 
  motivo: string 
}

export const PREVIA_ESTADO: Record<NivelSaude, EstadoRelogio> = {
  0: { fc: 73, spo2: 98, homeostase: 94, motivo: 'Mente estável' },
  1: { fc: 99, spo2: 94, homeostase: 70, motivo: 'Estresse moderado' },
  2: { fc: 123, spo2: 89, homeostase: 19, motivo: 'FC alta e SpO₂ baixa' },
}

export type CicloNoRelogio = { dia: number; fase: string } | { metodo: string }

export const CICLO_NO_RELOGIO: Record<string, CicloNoRelogio> = {
  sarah: { dia: 16, fase: 'lútea' }
}
