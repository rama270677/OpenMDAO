"""Define the ExplicitComponent class."""

from __future__ import division

import collections

import numpy
from six import string_types

from openmdao.core.component import Component


class ExplicitComponent(Component):
    """Class to inherit from when all output variables are explicit."""

    def _apply_nonlinear(self):
        """See System._apply_nonlinear."""
        inputs = self._inputs
        outputs = self._outputs
        residuals = self._residuals

        residuals.set_vec(outputs)

        self._inputs.scale(self._scaling_to_phys['input'])
        self._outputs.scale(self._scaling_to_phys['output'])

        self.compute(inputs, outputs)

        self._inputs.scale(self._scaling_to_norm['input'])
        self._outputs.scale(self._scaling_to_norm['output'])

        residuals -= outputs
        outputs += residuals

    def _solve_nonlinear(self):
        """See System._solve_nonlinear."""
        inputs = self._inputs
        outputs = self._outputs
        residuals = self._residuals

        residuals.set_const(0.0)

        self._inputs.scale(self._scaling_to_phys['input'])
        self._outputs.scale(self._scaling_to_phys['output'])

        self.compute(inputs, outputs)

        self._inputs.scale(self._scaling_to_norm['input'])
        self._outputs.scale(self._scaling_to_norm['output'])

    def _apply_linear(self, vec_names, mode, var_inds=None):
        """See System._apply_linear."""
        for vec_name in vec_names:
            with self._matvec_context(vec_name, var_inds, mode) as vecs:
                d_inputs, d_outputs, d_residuals = vecs
                self._jacobian._system = self
                self._jacobian._apply(d_inputs, d_outputs, d_residuals,
                                      mode)

                self._inputs.scale(self._scaling_to_phys['input'])
                self._outputs.scale(self._scaling_to_phys['output'])
                d_inputs.scale(self._scaling_to_phys['input'])
                d_residuals.scale(self._scaling_to_phys['residual'])

                d_residuals *= -1.0

                self.compute_jacvec_product(
                    self._inputs, self._outputs,
                    d_inputs, d_residuals, mode)

                d_residuals *= -1.0

                self._inputs.scale(self._scaling_to_norm['input'])
                self._outputs.scale(self._scaling_to_norm['output'])
                d_inputs.scale(self._scaling_to_norm['input'])
                d_residuals.scale(self._scaling_to_norm['residual'])

    def _solve_linear(self, vec_names, mode):
        """See System._solve_linear."""
        for vec_name in vec_names:
            d_outputs = self._vectors['output'][vec_name]
            d_residuals = self._vectors['residual'][vec_name]
            if mode == 'fwd':
                d_outputs.set_vec(d_residuals)
            elif mode == 'rev':
                d_residuals.set_vec(d_outputs)

    def _linearize(self, initial=False):
        """See System._linearize."""
        self._jacobian._system = self

        self._inputs.scale(self._scaling_to_phys['input'])
        self._outputs.scale(self._scaling_to_phys['output'])

        self.compute_jacobian(self._inputs, self._outputs, self._jacobian)

        self._inputs.scale(self._scaling_to_norm['input'])
        self._outputs.scale(self._scaling_to_norm['output'])

        for op_name in self._variable_myproc_names['output']:
            size = len(self._outputs._views_flat[op_name])
            ones = numpy.ones(size)
            arange = numpy.arange(size)
            self._jacobian[op_name, op_name] = (ones, arange, arange)

        for op_name in self._variable_myproc_names['output']:
            for ip_name in self._variable_myproc_names['input']:
                if (op_name, ip_name) in self._jacobian:
                    self._jacobian._negate((op_name, ip_name))

        self._jacobian._precompute_iter()
        if not initial and self._jacobian._top_name == self.path_name:
            self._jacobian._update()

    def compute(self, inputs, outputs):
        """Compute outputs given inputs.

        Args
        ----
        inputs : Vector
            unscaled, dimensional input variables read via inputs[key]
        outputs : Vector
            unscaled, dimensional output variables read via outputs[key]
        """
        pass

    def compute_jacobian(self, inputs, outputs, jacobian):
        """Compute sub-jacobian parts / factorization.

        Args
        ----
        inputs : Vector
            unscaled, dimensional input variables read via inputs[key]
        outputs : Vector
            unscaled, dimensional output variables read via outputs[key]
        jacobian : Jacobian
            sub-jac components written to jacobian[output_name, input_name]
        """
        pass

    def compute_jacvec_product(self, inputs, outputs,
                               d_inputs, d_outputs, mode):
        r"""Compute jac-vector product.

        If mode is:
            'fwd': d_inputs \|-> d_outputs

            'rev': d_outputs \|-> d_inputs

        Args
        ----
        inputs : Vector
            unscaled, dimensional input variables read via inputs[key]
        outputs : Vector
            unscaled, dimensional output variables read via outputs[key]
        d_inputs : Vector
            see inputs; product must be computed only if var_name in d_inputs
        d_outputs : Vector
            see outputs; product must be computed only if var_name in d_outputs
        mode : str
            either 'fwd' or 'rev'
        """
        pass
