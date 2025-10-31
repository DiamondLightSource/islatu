"""
Module for testing the config loader module
"""
import copy
from schema import SchemaError
import pytest
from pytest_lazyfixture import lazy_fixture as lazy
from islatu.config_loader import check_config_schema




@pytest.mark.parametrize(
    'recipe',
    [lazy('example_recipe_dcd_01')]
)

def test_config_schema(recipe):
    """
    Tests the schema checking function
    """
    
    #test initial good yaml
    check_config_schema(recipe)

    #modify recipe with bad options
    testrecipe =copy.deepcopy(recipe)
    testrecipe.setdefault('ajustments', {})
    testrecipe['ajustments']['new_axis_type']=0

    with pytest.raises(SchemaError):
        check_config_schema(testrecipe)
    
    testrecipe =copy.deepcopy(recipe)

