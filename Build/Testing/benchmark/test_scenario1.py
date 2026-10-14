import math
import unittest
from plot_scenario1 import student_t_pvalue, paired_t


class StudentTTests(unittest.TestCase):
    def test_cauchy_distribution_identity(self):
        for value in (0.1, 0.5, 1, 2, 10):
            expected=1-2*math.atan(value)/math.pi
            self.assertAlmostEqual(student_t_pvalue(value,1),expected,places=12)

    def test_chest_gorillapod_regression(self):
        # Independent numerical integration of the Student-t PDF, df=32.
        df=32;t=1.629376339780705;n=20000;h=t/n
        norm=math.exp(math.lgamma((df+1)/2)-math.lgamma(df/2))/math.sqrt(df*math.pi)
        f=lambda x:norm*(1+x*x/df)**(-(df+1)/2)
        integral=h/3*(f(0)+f(t)+4*sum(f(i*h) for i in range(1,n,2))+2*sum(f(i*h) for i in range(2,n,2)))
        self.assertAlmostEqual(student_t_pvalue(t,df),1-2*integral,places=11)
        self.assertGreater(student_t_pvalue(t,df),.05)

    def test_symmetry_and_limits(self):
        self.assertEqual(student_t_pvalue(0,32),1)
        self.assertEqual(student_t_pvalue(math.inf,32),0)
        self.assertEqual(student_t_pvalue(2.4,32),student_t_pvalue(-2.4,32))

    def test_identical_pairs(self):
        result=paired_t([1,2,3],[1,2,3])
        self.assertEqual(result['t'],0)
        self.assertEqual(result['p'],1)


if __name__=='__main__':unittest.main()
