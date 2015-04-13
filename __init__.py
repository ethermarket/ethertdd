from ethereum import tester

class EvmContract(object):
    def __init__(self, compiled_abi, compiled_code, sender=tester.k0,
                 endowment=0, gas=None, state=None):
        if not state:
            state = tester.state()

        self.state = state
        self.address = self.state.evm(compiled_code, sender, endowment, gas)
        assert len(self.state.block.get_code(self.address)), \
            "Contract code empty"
        self._translator = tester.abi.ContractTranslator(compiled_abi)

        def kall_factory(f):

            def kall(*args, **kwargs):
                self.state.block.log_listeners.append(
                    lambda log: self._translator.listen(log))
                o = self.state._send(kwargs.get('sender', tester.k0),
                                 self.address,
                                 kwargs.get('value', 0),
                                 self._translator.encode(f, args),
                                 **tester.dict_without(kwargs, 'sender',
                                                'value', 'output'))
                self.state.block.log_listeners.pop()
                # Compute output data
                if kwargs.get('output', '') == 'raw':
                    outdata = o['output']
                elif not o['output']:
                    outdata = None
                else:
                    outdata = self._translator.decode(f, o['output'])
                    outdata = outdata[0] if len(outdata) == 1 \
                        else outdata
                # Format output
                if kwargs.get('profiling', ''):
                    return dict_with(o, output=outdata)
                else:
                    return outdata
            return kall

        for f in self._translator.function_data:
            vars(self)[f] = kall_factory(f)
