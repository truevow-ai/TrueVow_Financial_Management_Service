"use client"

import React from 'react'
import { Button as UIButton } from '../ui/button'

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'default' | 'destructive' | 'outline' | 'secondary' | 'ghost' | 'link'
  size?: 'default' | 'sm' | 'lg' | 'icon'
}

export function Button({ variant = 'default', size = 'default', className, ...props }: ButtonProps) {
  return <UIButton variant={variant} size={size} className={className} {...props} />
}
