import scmcoat.core.fair as fair


def test_fairmodel_run():
    """Test that FaIRModel.run runs on test_emissions without throwing exception
    """
    # initialize the model
    fm = fair.FaIRModel()

    # Open up the test emissions to use as a demo
    emissions = fm.get_test_emissions()

    # run FaIR with these emissions under its default settings
    response = fm.run(emissions)
