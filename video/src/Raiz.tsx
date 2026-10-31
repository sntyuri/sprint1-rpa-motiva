import React from "react";
import { Audio, Composition, Series, staticFile } from "remotion";
import { CENAS } from "./cenas";

const FPS = 30;
const quadros = (seg: number) => Math.round(seg * FPS);
const total = CENAS.reduce((soma, c) => soma + quadros(c.seg), 0);

const Demo: React.FC = () => (
  <>
    <Audio src={staticFile("narracao.wav")} />
    <Series>
      {CENAS.map(({ id, seg, C }) => (
        <Series.Sequence key={id} durationInFrames={quadros(seg)} premountFor={FPS}>
          <C />
        </Series.Sequence>
      ))}
    </Series>
  </>
);

export const Raiz: React.FC = () => (
  <Composition id="Demo" component={Demo} durationInFrames={total} fps={FPS} width={1920} height={1080} />
);
