// Descrição de cada sinal vital mostrado nos cards: nome, unidade, ícone, fonte e como formatar o valor

import type { Component } from 'vue'
import { Activity, Droplet, Gauge, Heart, Waves, Wind } from 'lucide-vue-next'
import type { ChaveSinal, Vitais } from '@/mocks/tripulacao'

export interface InfoSinal {
  chave: ChaveSinal
  nome: string
  unidade: string
  fonte: string 
  icone: Component
  corIcone: string 
  formatar: (v: Vitais) => string
}

const milhar = (n: number) => Math.round(n).toLocaleString('pt-BR')

export const SINAIS: InfoSinal[] = [
  {
    chave: 'fc',
    nome: 'Frequência cardíaca',
    unidade: 'bpm',
    fonte: 'Relógio · PPG + ECG',
    icone: Heart,
    corIcone: 'var(--crit)',
    formatar: (v) => String(Math.round(v.fc)),
  },
  {
    chave: 'spo2',
    nome: 'Saturação de O₂',
    unidade: '%',
    fonte: 'Relógio · oxímetro',
    icone: Waves,
    corIcone: 'var(--acento)',
    formatar: (v) => String(Math.round(v.spo2)),
  },
  {
    chave: 'pa',
    nome: 'Pressão arterial',
    unidade: 'mmHg',
    fonte: 'Manguito do kit médico',
    icone: Gauge,
    corIcone: 'var(--acento)',
    formatar: (v) => `${Math.round(v.paSis)}/${Math.round(v.paDia)}`,
  },
  {
    chave: 'resp',
    nome: 'Respiração',
    unidade: 'irpm',
    fonte: 'Patch torácico',
    icone: Wind,
    corIcone: 'var(--acento)',
    formatar: (v) => String(Math.round(v.resp)),
  },
  {
    chave: 'hrv',
    nome: 'Variabilidade cardíaca',
    unidade: 'ms',
    fonte: 'Relógio · PPG',
    icone: Activity,
    corIcone: 'var(--acento)',
    formatar: (v) => String(Math.round(v.hrv)),
  },
  {
    chave: 'agua',
    nome: 'Hidratação',
    unidade: 'ml',
    fonte: 'Registro + estimativa',
    icone: Droplet,
    corIcone: 'var(--agua)',
    formatar: (v) => milhar(v.agua),
  },
]
