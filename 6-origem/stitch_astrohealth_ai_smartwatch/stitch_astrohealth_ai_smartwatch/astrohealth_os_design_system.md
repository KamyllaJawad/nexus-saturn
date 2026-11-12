---
name: "AstroHealth OS"
description: "Sistema de design biométrico com tema OLED escuro, feedback cromático em tempo real (Ótimo, Atenção, Crítico) e avatar de astronauta para smartwatch."
---

## Overview

AstroHealth OS é um sistema operacional e assistente biométrico inteligente em tempo real para smartwatches de alta performance. Inspirado na telemetria aeroespacial e no monitoramento de astronautas da NASA e ESA, o sistema traduz dados fisiológicos complexos (frequência cardíaca, ECG, estresse/saúde mental, sono profundo/REM, ciclo menstrual, hidratação, VO2 max e atividade física) em um avatar de astronauta interativo e 3 indicadores imediatos de estado corporal: Ótimo (Ciano/Verde Esmeralda), Atenção/Bem (Âmbar Solar) e Ruim/Crítico (Rubi Carmesim).

O estilo combina precisão de painel de instrumentação médica de alta tecnologia com a delicadeza e empatia de uma IA companheira de saúde ("Cosmo AI"). Possui fundo preto absoluto OLED (#05070E) para economia de energia extrema e contraste cirúrgico em telas diminutas de relógio.

## Colors

A paleta prioriza preto profundo OLED, superfícies de vidro fosco sutis e iluminação biométrica vibrante que atende aos padrões de contraste WCAG AA.

- **Primary:** Ciano bio-elétrico (#00E5FF) que simboliza homeostase e dados ativos de IA.
- **Success / Ótimo:** Verde Esmeralda (#10B981) para sinais vitais estáveis e alta recuperação.
- **Warning / Atenção:** Âmbar Solar (#F59E0B) para estresse elevado, fadiga ou hidratação pendente.
- **Danger / Ruim:** Rubi Carmesim (#EF4444) para sobrecarga cardíaca, privação severa ou anomalias.
- **Hydration:** Azul Cobalto (#3B82F6) para hidratação e fluidos corporais.
- **Cycle:** Rosa Orquídea (#EC4899) para ovulação e ciclo menstrual.
- **Sleep:** Violeta Estelar (#8B5CF6) para estágios de sono e regeneração neural.

```yaml
colors:
  accent: "#00E5FF"
  optimal: "#10B981"
  attention: "#F59E0B"
  critical: "#EF4444"
  hydration: "#3B82F6"
  cycle: "#EC4899"
  sleep: "#8B5CF6"
  light:
    primary: "#006878"
    on-primary: "#FFFFFF"
    surface: "#080B14"
    on-surface: "#F3F4F6"
  dark:
    primary: "#00E5FF"
    on-primary: "#051820"
    surface: "#05070E"
    on-surface: "#F8FAFC"
```

## Typography

Utiliza **Space Grotesk** para dados biométricos numéricos, títulos de telemetria e botões de comando, e **Inter** para leituras médicas, prompts da IA e legibilidade perfeita em fontes condensadas de relógio.

```yaml
typography:
  display-lg:
    fontFamily: "Space Grotesk"
    fontSize: 28px
    fontWeight: 700
    lineHeight: 32px
    letterSpacing: -0.5px
  display-lg-mobile:
    fontFamily: "Space Grotesk"
    fontSize: 24px
    fontWeight: 700
    lineHeight: 28px
    letterSpacing: -0.5px
  headline-lg:
    fontFamily: "Space Grotesk"
    fontSize: 20px
    fontWeight: 600
    lineHeight: 24px
    letterSpacing: -0.2px
  headline-lg-mobile:
    fontFamily: "Space Grotesk"
    fontSize: 18px
    fontWeight: 600
    lineHeight: 22px
    letterSpacing: -0.2px
  body-md:
    fontFamily: "Inter"
    fontSize: 13px
    fontWeight: 400
    lineHeight: 17px
    letterSpacing: 0px
  label-lg:
    fontFamily: "Space Grotesk"
    fontSize: 12px
    fontWeight: 600
    lineHeight: 16px
    letterSpacing: 0.5px
  label-sm:
    fontFamily: "Inter"
    fontSize: 10px
    fontWeight: 500
    lineHeight: 13px
    letterSpacing: 0.2px
```

## Layout & Spacing

Desenvolvido para telas compactas de smartwatch (390px–420px de viewport). Usa sistema de raio responsivo para telas circulares (com margens radiais de 24px) e quadradas/squircles com cantos ultra-arredondados (raio de 44px).

```yaml
spacing:
  gutter-xs: 4px
  gutter-sm: 8px
  gutter-md: 12px
  gutter-lg: 16px
  gutter-xl: 20px
  section: 24px
  page-margin: 16px
```

## Elevation & Depth

Superfícies de fundo OLED profundo com cartões em tons de ardósia espacial escurecida (`#0F172A` / `#111827`) e bordas ultra-finas de 1px com baixa opacidade para isolamento tátil. Brilhos bioluminescentes discretos nas cores de status para indicar alertas em tempo real.

## Shapes

Bordas arredondadas ergonômicas para toque com polegar e dedo indicador na tela de pulso.

```yaml
rounded:
  sm: 6px
  DEFAULT: 12px
  md: 16px
  lg: 20px
  xl: 28px
  full: 9999px
```

## Motion & Micro-interaction

Micro-interações de pulso cardíaco para o avatar do astronauta e transições fluidas de rolagem digital rápida para a coroa do relógio.

```yaml
motion:
  state-change:
    duration: 150ms
    delay: 0ms
    timingFunction: cubic-bezier(0.4, 0, 0.2, 1)
  pulse-vital:
    duration: 1000ms
    delay: 0ms
    timingFunction: ease-in-out
```

## Voice & Content Strategy

A IA assistente ("Cosmo") fala em tom clínico-empático, objetivo, focado em ações acionáveis imediatas no presente ("Beba 250ml agora", "Respire fundo por 60s", "Zona anaeróbica atingida"). Números sempre com unidades precisas (bpm, %, ml, kcal).

## Components

Component implementations live as individual HTML sticker sheet files in
`components/`. Each file contains the canonical, styled HTML components with
`<!-- COMPONENT: name -->` comment markers. Read each file before use.

- **Badge** → `@components/badge.html`: `badge-numeric`, `badge-dot`
- **Button** → `@components/button.html`: `button-primary`, `button-icon`, `button-with-icon`
- **Card** → `@components/card.html`: `card-elevated`, `card-action`, `card-interactive`, `card-interactive-2`
