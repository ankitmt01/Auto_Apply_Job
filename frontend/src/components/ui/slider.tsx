
import React from 'react';
type Props = { value: number[], onValueChange:(v:number[])=>void, min?:number, max?:number, step?:number };
export const Slider: React.FC<Props> = ({value, onValueChange, min=0, max=100, step=1}) => {
  return <input type="range" min={min} max={max} step={step} value={value[0]} onChange={(e)=>onValueChange([Number(e.target.value)])} className="w-full"/>;
};
