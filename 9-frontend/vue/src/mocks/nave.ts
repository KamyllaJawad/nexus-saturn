// Dados mockados para utilizar sem o back

export interface StatusNave {
  houstonOnline: boolean 
  atrasoHouston: string 
  tripulantes: number
  co2: number
  // Sem médico a bordo o painel é do Marcus como CMO (vem de /api/missao).
  titulo?: string
  subtitulo?: string
}

export const statusNaveMock: StatusNave = {
  houstonOnline: true,
  atrasoHouston: '< 1 s',
  tripulantes: 4,
  co2: 2.4,
}
