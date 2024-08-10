# =========== Copyright 2023 - 2024 Startr.LLC & CAMEL-AI.org. All Rights Reserved. ===========
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# =========== Copyright 2023 - 2024 @ Startr.LLC & CAMEL-AI.org. All Rights Reserved. ===========

import argparse
import logging
import os
import sys
from typing import NoReturn, Tuple, List

from camel.typing import ModelType # imports our models from model_config.yaml

# Constants
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = os.path.join(ROOT_DIR, "CompanyConfig")
DEFAULT_CONFIG_DIR = os.path.join(CONFIG_DIR, "Default")

CONFIG_FILES = [
    "ChatChainConfig.json",
    "PhaseConfig.json",
    "RoleConfig.json"
]

sys.path.append(ROOT_DIR)

from chatdev.chat_chain import ChatChain

try:
    from openai.types.chat.chat_completion_message_tool_call import ChatCompletionMessageToolCall
    from openai.types.chat.chat_completion_message import FunctionCall

    openai_new_api = True  # new openai api version
except ImportError:
    openai_new_api = False  # old openai api version
    print(
        "Warning: Your OpenAI version is outdated. \n "
        "Please update as specified in requirement.txt. \n "
        "The old API interface is no longer supported.")


def get_model_choices() -> List[str]:
    """
    Get a list of model names from the ModelType enum.

    Returns:
        List[str]: A list of model names as strings.
    """
    return [model.name for model in ModelType]





def check_api_key() -> NoReturn:
    """
    Check if the OpenAI API key is set and exit if it's not.

    Raises:
        SystemExit: If the API key is not set or is empty.
    """
    if 'OPENAI_API_KEY' not in os.environ or os.environ['OPENAI_API_KEY'] == "":
        print("\033[94m")
        print("Error: OPENAI_API_KEY environment variable is not set or is empty.")
        print("To fix, please set your OpenAI API key by doing one of the following:")
        print("  1. Run `export OPENAI_API_KEY=\"your-api-key-here\"` in your terminal.")
        print("  2. Add `OPENAI_API_KEY=your-api-key-here` to a new line in a `.env` file in your project's root directory.")
        print("If you don't have an API key, sign up at https://platform.openai.com/signup")
        print("\033[0m")
        sys.exit(1)


def get_config(company: str) -> Tuple[str, str, str]:
    """
    Get paths to configuration files for a company.

    This function checks if custom configuration files exist for the given company.
    If custom files are found, it returns their paths. If not, it returns paths to
    default configuration files.

    Args:
        company (str): The name of the company to get configuration files for. 
                    Custom configurations are stored in a folder named after the company.

    Returns:
        Tuple[str, str, str]: Paths to three configuration files:
            - Path to the main config file
            - Path to the phase config file
            - Path to the role config file

    Note:
        Configuration files are in JSON format.

        If a custom file is missing, the function will use the default file instead.
    """
    config_dir = os.path.join(CONFIG_DIR, company)
    config_paths = []

    for config_file in CONFIG_FILES:
        company_config_path = os.path.join(config_dir, config_file)
        default_config_path = os.path.join(DEFAULT_CONFIG_DIR, config_file)

        if os.path.exists(company_config_path):
            config_paths.append(company_config_path)
        else:
            config_paths.append(default_config_path)

    return tuple(config_paths)

def get_CompanyConfigs() -> List[str]:
    """
    Get a list of company names from the CompanyConfig directory.

    Returns:
        List[str]: A list of company names as strings.
    """
    #return os.listdir(CONFIG_DIR) note we should only return directories
    return [name for name in os.listdir(CONFIG_DIR) if os.path.isdir(os.path.join(CONFIG_DIR, name))]

def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments for the Startr.Team ChatChain.

    Returns:
        argparse.Namespace: Parsed command-line arguments.
    """
    parser = argparse.ArgumentParser(description='Startr.Team ChatChain')
        
        # Dictionary to hold argument configurations
    args_config = {
        'local': (bool, False, "Use local Ollama API instead of OpenAI API"),
        'config': (str, "Default", "CompanyConfig name loading settings(Choices: {})".format(", ".join(get_CompanyConfigs()))),
        'org': (str, "DefaultOrganization", "Organization name for software generation"),
        'task': (str, "Develop a basic Website.", "Software prompt"),
        'name': (str, "Website", "Software name for generation"),
        'model': (str, "GPT_3_5_TURBO_NEW", "GPT Model (choices: {})".format(", ".join(get_model_choices()))),
        'path': (str, "", "Directory for incremental mode"),
    }

    # Loop through each argument configuration
    for arg, (type_, default, help_text) in args_config.items():
        flag = f'--{arg}'  # Infer long flag based on key name
        short_flag = f'-{arg[0]}'  # Infer short flag based on the first character of the key name
        """
        if arg == 'model':
            choices = get_model_choices()
            help_text = f"{help_text}"
            parser.add_argument(
                short_flag,
                flag,
                type=type_,
                default=default,
                help=help_text
            )
        else:
        """
            # Add the argument to the parser with the given configuration
        parser.add_argument(
            short_flag,
            flag,
            type=type_,
            default=default,
            help=help_text
        )

    
    return parser.parse_args()

def main():
    """
    Main function to execute the Startr.Team ChatChain process.
    """
    args = parse_arguments()
    check_api_key()

    config_path, config_phase_path, config_role_path = get_config(args.config)

    chat_chain = ChatChain(
        use_ollama=args.local,
        config_path=config_path,
        config_phase_path=config_phase_path,
        config_role_path=config_role_path,
        task_prompt=args.task,
        project_name=args.name,
        org_name=args.org,
        model_type=ModelType[args.model],
        code_path=args.path
    )

    logging.basicConfig(
        filename=chat_chain.log_filepath,
        level=logging.INFO,
        format='[%(asctime)s %(levelname)s] %(message)s',
        datefmt='%Y-%d-%m %H:%M:%S',
        encoding="utf-8"
    )

    chat_chain.pre_processing()
    chat_chain.recruit_team()
    chat_chain.execute_chain()
    chat_chain.post_processing()


if __name__ == "__main__":
    main()