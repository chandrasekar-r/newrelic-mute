from newrelic import *

def run():
        nr = NewRelicRule()

        try:
            nr.create_mute_rule()  # Mute Rule will be enabled by default when the rule is created.
        except Exception as ex:
            err = "There's an error in creating the Mutation Rule. Please visit the Newrelic UI. \n%s " % ex
            print(err)
            pass

        try:
            nr.toggle_mute_rule(mutation_id, is_enabled='false') #Mutation_id = Id created using create_mute_rule function
        except Exception as ex:
            err = "There's an error in disabling the Mutation Rule. Please visit the Newrelic UI. \n%s " % ex
            print(err)
            pass


        try:
            nr.toggle_mute_rule(mutation_id, is_enabled='true')
        except Exception as ex:
            err = "There's an error in enabling the Mutation Rule. Please visit the Newrelic UI. \n%s " % ex
            print(err)
            pass