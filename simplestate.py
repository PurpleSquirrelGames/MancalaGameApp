class StateMachine(object):

    def __init__(self, debug=False):
        global DEBUG
        self.state_dict = {}
        self.current_state = None
        self.ref = {}
        self.DEBUG = debug

    def register_state(self, state):
        if "state_name" not in dir(state):
            raise KeyError("Unable to locate 'state_name' in state object {}.".format(state))
        state_name = state.state_name
        state.change_state = self.change_state # binding parent function to child
        state.get_state = self.get_state
        state.ref = self.ref
        self.state_dict[state_name] = state
        if self.DEBUG: print "REGISTERED {} {}".format(state_name, state)

    def start(self, state_name):
        self.change_state(state_name)

    def bind_reference(self, key, target):
        self.ref[key] = target

    def change_state(self, state_name):
        state_name = str(state_name)
        if state_name not in self.state_dict:
            raise KeyError("Unable to locate a state of '{}'.".format(state_name))
        if self.current_state is not None:
            if "on_exit" in dir(self.state_dict[self.current_state]):
                # obliterate the 'change state' function to prevent use
                self.state_dict[self.current_state].change_state = None
                self.state_dict[self.current_state].on_exit()
                # restore the change state function
                self.state_dict[self.current_state].change_state = self.change_state
        # Special NOTE: because 'on_entry' might also invoke 'change_state', it is
        # critical that the state_name be changed FIRST, or you will end up in
        # the wrong state due to recursion
        previous_state = self.current_state
        self.current_state = state_name
        if self.DEBUG: print "STATE CHANGE {} -> {}".format(previous_state, state_name)
        if "on_entry" in dir(self.state_dict[state_name]):
            self.state_dict[state_name].on_entry()
            # print "STATE AFTER ON_ENTRY", self.current_state
        return self.get_state()

    def get_state(self):
        return self.current_state

    @property
    def same_state(self):
        return self.current_state

    def input(self, input_name, *args, **kwargs):
        if self.DEBUG: print "STATE {} RECEIVED INPUT {} {} {}".format(self.current_state, input_name, args, kwargs)
        if self.current_state is None:
            raise IOError("StateMachine has not started yet, so it cannot accept '{}' input.".format(input_name))
        if "input" in dir(self.state_dict[self.current_state]):
            return self.state_dict[self.current_state].input(input_name, *args, **kwargs)
        return None


class State(object):
    
    def __init__(self, state_name):
        self.state_name = str(state_name)

    def on_entry(self):
        pass

    def on_exit(self):
        '''
        Calling 'self.change_state' is forbidden in the 'on_exit' routine. Doing so
        would cause an improper sequence of events that are difficult to predict.
        '''
        pass

    def input(self, input_name, *args, **kwargs):
        pass

    def get_state(self):
        return None

    @property
    def same_state(self):
        return self.get_state()

