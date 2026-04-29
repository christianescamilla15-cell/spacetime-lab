/**
 * KaTeX wrapper components — block and inline LaTeX rendering.
 *
 * Spacetime Lab convention: every numerical result must be paired with
 * its LaTeX representation. These components keep that uniform across
 * every page.
 */

import { InlineMath, BlockMath } from 'react-katex'
import 'katex/dist/katex.min.css'

export function Tex({ children }) {
  return <InlineMath math={children} />
}

export function TexBlock({ children }) {
  return <BlockMath math={children} />
}
