// Gatilhos de cenário (POST /api/simulador/cenario), usados na sala de simulação e
// fora do relógio. O cenário só muda o sinal; quem detecta são os modelos.

export type Gatilho = [rotulo: string, cenario: string, tripulante: string | null]

export const SINAIS_RELOGIO: Gatilho[] = [
  ['Fibrilação atrial · Sarah', 'fa', 'sarah'],
  ['Relógio folgado · Sarah', 'sensor_solto', 'sarah'],
  ['Combinação fora do padrão · Kenji', 'combinacao', 'kenji'],
  ['Ciclo · Sarah (supressão)', 'ciclo', 'sarah'],
  ['Ciclo · Elena (sem método)', 'ciclo', 'elena'],
  ['Mesmo desvio · Kenji (sem calendário)', 'ciclo', 'kenji'],
  ['Voltar à rotina', 'rotina', null],
]

export const EVENTOS_BORDO: Gatilho[] = [
  ['Tempestade solar', 'tempestade_solar', null],
  ['Queda de humor', 'humor', 'sarah'],
  ['Prontidão EVA', 'eva', null],
  ['Dor de cabeça + CO₂', 'dor_de_cabeca', 'sarah'],
  ['Hora de dormir', 'modo_noite', 'sarah'],
]

// A família na Terra (app Terra-Órbita): cada ação viaja pelo link até o relógio.
export const ACOES_FAMILIA: [rotulo: string, tipo: 'brinde' | 'corrida' | 'mensagem'][] = [
  ['Brinde hídrico da Ana', 'brinde'],
  ['Corrida do Lucas · 5 km', 'corrida'],
  ['Áudio do Lucas', 'mensagem'],
]
