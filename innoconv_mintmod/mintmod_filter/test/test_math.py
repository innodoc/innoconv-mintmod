# pylint: disable=missing-docstring,invalid-name

import unittest
import panflute as pf
from innoconv_mintmod.mintmod_filter.math import handle_math


class TestHandleSubstitutions(unittest.TestCase):
    def test_handle_math_substitutions(self):
        """Math substitutions should work"""
        elem_math = pf.Math(r"\N \Q {\R}")
        elem_math_repl = handle_math(elem_math)
        self.assertEqual(elem_math_repl.text, r"\mathbb{N} \mathbb{Q} {\mathbb{R}}")


class TestHandleIrregular(unittest.TestCase):
    def test_handle_math_mvector(self):
        """MVector: commands in arguments"""
        elem_math = pf.Math(r"x^2 \MVector{2\\-\Mtfrac{5}{2}\\-2}")
        elem_math_repl = handle_math(elem_math)
        self.assertEqual(
            elem_math_repl.text,
            r"x^2 \begin{pmatrix}2\\-\tfrac{5}{2}\\-2\end{pmatrix}",
        )

    def test_handle_math_mpointtwo(self):
        """MPointTwo: commands in arguments"""
        elem_math = pf.Math(r"\MPointTwo{\frac{3}{2}}{1+\frac{\sqrt{3}}{2}} " "x_2")
        elem_math_repl = handle_math(elem_math)
        self.assertEqual(
            elem_math_repl.text,
            r"(\frac{3}{2}\coordsep 1+\frac{\sqrt{3}}{2}) x_2",
        )

    def test_handle_math_mpointtwo_big(self):
        r"""MPointTwo[\big]: commands in arguments"""
        elem_math = pf.Math(r"\MPointTwo[\Big]{\frac{3}{2}}{1+\frac{\sqrt{3}}{2}}")
        elem_math_repl = handle_math(elem_math)
        self.assertEqual(
            elem_math_repl.text,
            r"\Big(\frac{3}{2}\coordsep 1+\frac{\sqrt{3}}{2}{}\Big)",
        )

    def test_handle_math_mpointtwo_parse_bug(self):
        r"""MPointTwo[\big]: a particular bug"""
        elem_math = pf.Math(r"\MPointTwo[\Big]{\frac{1}{n}}{0}\MCondSetSep")
        elem_math_repl = handle_math(elem_math)
        self.assertEqual(
            elem_math_repl.text,
            r"\Big(\frac{1}{n}\coordsep 0{}\Big) {\,}:{\,}",
        )

    def test_handle_math_mpointtwoas(self):
        r"""MPointTwoAS: commands in arguments"""
        elem_math = pf.Math(r"\MPointTwoAS{-\sqrt6}{-\frac12\sqrt6}")
        elem_math_repl = handle_math(elem_math)
        self.assertEqual(
            elem_math_repl.text,
            r"\left(-\sqrt6\coordsep -\frac12\sqrt6\right)",
        )

    def test_handle_math_mpointthree(self):
        r"""MPointThree: commands in arguments"""
        elem_math = pf.Math(
            r"\MPointThree{x = \Mtfrac{2}{19}}{y = - \Mtfrac{5}{19}}"
            r"{z = \Mtfrac{2}{19}}"
        )
        elem_math_repl = handle_math(elem_math)
        self.assertEqual(
            elem_math_repl.text,
            r"(x = \tfrac{2}{19}\coordsep y = - \tfrac{5}{19}\coordsep "
            r"z = \tfrac{2}{19})",
        )

    def test_handle_math_mpointthree_big(self):
        r"""MPointThree[\big]: commands in arguments"""
        elem_math = pf.Math(r"\MPointThree[\Big]{\frac{3}{2}}{1}{2}")
        elem_math_repl = handle_math(elem_math)
        self.assertEqual(
            elem_math_repl.text,
            r"\Big(\frac{3}{2}\coordsep 1\coordsep 2{}\Big)",
        )

    def test_handle_math_multiple(self):
        r"""multiple commands in one math string"""
        elem_math = pf.Math(
            r"z=\MPointThree{\frac{1}{2}}{3}{\sqrt{2}};"
            r"q=\MPointTwoAS{2}{1+\frac{\sqrt{3}}{2}};"
            r"f(x)=x^2"
        )
        elem_math_repl = handle_math(elem_math)
        self.assertEqual(
            elem_math_repl.text,
            r"z=(\frac{1}{2}\coordsep 3\coordsep \sqrt{2});"
            r"q=\left(2\coordsep 1+\frac{\sqrt{3}}{2}\right);"
            r"f(x)=x^2",
        )

    def test_handle_math_mcases(self):
        r"""mcases: commands in arguments"""
        elem_math = pf.Math(
            r"\MCases{\text{Term} & \text{falls}\;\text{Term}\geq 0\\ "
            r"-\text{Term} & \text{falls}\;\text{Term}<0}"
        )
        elem_math_repl = handle_math(elem_math)
        self.assertEqual(
            elem_math_repl.text,
            r"\left\lbrace{\begin{array}{rl} \text{Term} & \text{falls}\;"
            r"\text{Term}\geq 0\\ -\text{Term} & \text{falls}\;\text{Term}<0 "
            r"\end{array}}\right.",
        )

    def test_handle_math_function(self):
        r"""function: commands in arguments"""
        elem_math = pf.Math(
            r"\function{h}{(-\frac{\pi}{2}\MIntvlSep \frac{\pi}{2})}"
            r"{\R}{\alpha}{\tan(\alpha)}"
        )
        elem_math_repl = handle_math(elem_math)
        self.assertEqual(
            elem_math_repl.text,
            r"h:\;\left\lbrace{\begin{array}{rcl} "
            r"(-\frac{\pi}{2}; \frac{\pi}{2}) &\longrightarrow &"
            r" \mathbb{R} \\ \alpha &\longmapsto  & \tan(\alpha) "
            r"\end{array}}\right.",
        )

    def test_handle_math_meinheit(self):
        r"""MEinheit"""
        elem_math = pf.Math(r"\MEinheit{kg} -58^{\circ}{\MEinheit[]{C}}")
        elem_math_repl = handle_math(elem_math)
        self.assertEqual(elem_math_repl.text, r"\, \mathrm{kg} -58^{\circ}{\mathrm{C}}")


class TestHandleMCaseEnv(unittest.TestCase):
    def test_handle_mcaseenv(self):
        """MMCaseEnv"""
        elem_math = pf.Math(
            r"|x| = \begin{MCaseEnv} x & \text{falls}\;x\geq 0 "
            r"\\ -x & \text{falls}\;x<0 \MDFPeriod \end{MCaseEnv}"
        )
        elem_math_repl = handle_math(elem_math)
        self.assertEqual(
            elem_math_repl.text,
            r"|x| = \left\lbrace\begin{array}{rl} x & \text{falls}\;x\geq 0 "
            r"\\ -x & \text{falls}\;x<0 \, . \end{array}\right.",
        )
