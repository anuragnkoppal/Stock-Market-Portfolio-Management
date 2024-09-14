# Stock Market Portfolio Management System

## About

This project is a Database Management System (DBMS) designed for stock market portfolio management. It includes a sophisticated suggestion system that analyzes both fundamental and technical signals to provide investment recommendations.

## Features

- **Portfolio Management**: Manage and track your stock investments.
- **Suggestion System**: Analyze fundamental and technical signals to suggest optimal investment strategies.
- **Interactive User Interface**: Built with modern web technologies for a seamless user experience.

## Technologies Used

- **Backend**: Flask
- **Frontend**: HTML, CSS, Bootstrap, JavaScript
- **Database**: MySQL

## Installation

To set up the project on your local machine, follow these steps:

1. **Clone the Repository**

    ```bash
    git clone https://github.com/your-username/your-repository.git
    ```

2. **Navigate to the Project Directory**

    ```bash
    cd your-repository
    ```

3. **Set Up a Virtual Environment**

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

4. **Install Dependencies**

    ```bash
    pip install -r requirements.txt
    ```

5. **Set Up the Database**

    - Import the provided MySQL schema into your MySQL database. Ensure you have a database created and configured as per the schema.
    - Place your database configuration details in the `config.py` file.

6. **Run the Application**

    ```bash
    python app.py
    ```

    Navigate to `http://127.0.0.1:5000` in your web browser to access the application.

## Relational Schema

The project's database schema is visualized in the `RELATIONAL SCHEMA.png` file. This diagram illustrates the relationships between different entities in the database.

## Contributing

Contributions to the project are welcome. Please fork the repository and submit a pull request with your proposed changes.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.

## Contact

For any inquiries or issues, please open an issue on GitHub or contact [your-email@example.com].

