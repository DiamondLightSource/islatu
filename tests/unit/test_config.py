"""
Module for testing the config loader module
"""
import copy
from schema import SchemaError
import pytest
from pytest_lazyfixture import lazy_fixture as lazy
from islatu.config_loader import check_config_schema,validate_new_axis




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



def test_validate_new_axis_valid():
    assert validate_new_axis('diff1chi') is True
    assert validate_new_axis('diff1delta') is True
    assert validate_new_axis('diff2alpha') is True

def test_validate_new_axis_invalid():
    with pytest.raises(ValueError) as excinfo:
        validate_new_axis('invalid_axis')
    assert "axis name invalid_axis not in valid new axis list" in str(excinfo.value)
