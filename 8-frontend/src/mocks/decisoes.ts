export interface Acao {
  chave: string
  rotulo: string
  feito: string
}

export interface Decisao {
  titulo: string
  texto: string
  acao: Acao
}

export interface Acompanhamento {
  titulo: string
  itens: string[]
  acao?: Acao
}

export interface CardDoTripulante {
  decisao?: Decisao
  acompanhamento: Acompanhamento
}

export const DECISOES: Record<string, CardDoTripulante> = {
  sarah: {
    acompanhamento: {
      titulo: 'Nenhuma decisão pendente',
      itens: [
        'ECG de rotina · Sarah · 14:00',
        'Densidade óssea (DXA) · Kenji · sexta',
        'Hidratação da Elena abaixo da meta · toque no nome dela para ver',
      ],
    },
  },
  marcus: {
    acompanhamento: {
      titulo: 'Autoavaliação do oficial médico',
      itens: [
        'Sinais estáveis: você está apto para atender.',
        'Sono de 7h05 e treino de 30 min concluído.',
        'Próxima autoavaliação no domingo.',
      ],
    },
  },
  elena: {
    acompanhamento: {
      titulo: 'Acompanhamento · Elena',
      itens: [
        'Hidratação em cerca de metade da meta; o lembrete das 08:30 ficou sem resposta.',
        'Duas noites seguidas com cerca de 6h10 de sono.',
        'Estresse moderado com a agenda de manutenção da cúpula cheia.',
      ],
      acao: {
        chave: 'elena-lembrete-agua',
        rotulo: 'Enviar lembrete de água ao relógio da Elena',
        feito: 'Lembrete enviado',
      },
    },
  },
  kenji: {
    decisao: {
      titulo: 'Treino resistivo · Kenji',
      texto:
        'Carga atual em 85% do previsto. A Cosmo sugere +5% nesta semana para frear a perda óssea e muscular.',
      acao: { chave: 'kenji-carga', rotulo: 'Aprovar carga da semana', feito: 'Carga aprovada' },
    },
    acompanhamento: {
      titulo: 'Acompanhamento · Kenji',
      itens: [
        'DXA (densidade óssea) marcada para sexta.',
        'Densidade óssea −1,2% em 3 meses, dentro do esperado para a missão.',
        'Todos os sinais na faixa ótima.',
      ],
    },
  },
}

export const KIT_MEDICO =
  'O₂ portátil em 92%, 18 eletrodos de ECG, 6 bolsas de soro, desfibrilador testado ontem. Antiarrítmicos: estoque para 2 tratamentos completos.'
