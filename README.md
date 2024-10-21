# Genomics AWS Cost Estimator

This cost calculator is tailored for Next-Generation Sequencing (NGS) data on the cloud, focusing on data storage and computational costs. It helps you estimate the expenses associated with storing and processing NGS data using AWS services, and contains information about data sizes and compute durations for approximation.

### Data Storage

Amazon Simple Storage Service (S3) is an object storage service devoted to secure storage, security, scalability, and performance.

Estimate the cost of storing your NGS data in AWS S3.

### Computational Costs

Amazon Elastic Compute Cloud (EC2) is a web service that provides resizable compute capacity in the cloud, allowing you to launch virtual servers (instances) with configurable CPU, memory, storage, and networking capacities, ideal for applications like processing Next-Generation Sequencing (NGS) data.

Calculate the expenses for processing NGS data using AWS EC2 instances and other computational resources.

## Prerequisites

Before you begin, ensure you have the following installed on your system:

- **Python 3.8 or higher**: You can download Python from the [official website](https://www.python.org/downloads/).
- **Conda**: A package and environment management system. You can download Conda from the [official website](https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html).n -m pip install --upgrade pip

## Development

### Setting Up the Environment

To set up the development environment, follow these steps:

1. **Create a Conda Environment**

   ```sh
   conda env create -f environment.yml
   ```

2. **Activate the Environment**

   ```sh
   conda activate shiny
   ```

### Run

To run the application locally, use the following command:

```sh
shiny run --port 8000 app.py
```

This will start the application, and you can access it in your web browser at http://localhost:8000.

### Export to Static Site Deployment

To export the project to a static site, run:

```sh
shinylive export . site
```

You should see the Calculator Dashboard. If you need to stop the server, press `Ctrl + C` in the terminal.

### Troubleshooting

If you encounter any issues during installation or running the application, consider the following steps:

- Ensure all dependencies are installed correctly.
- Check for any syntax or import errors in your Python files.
- Verify that your virtual environment is activated.
- Consult the application's documentation or support channels.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

We welcome contributions! Please see the [CONTRIBUTING](CONTRIBUTING.md) file for guidelines on how to get involved.

## Contact

If you have any questions or feedback, feel free to reach out:

- **Website**: [https://www.gedac.org/](https://www.gedac.org/)
- **GitHub Issues**: [https://github.com/CSI-Genomics-and-Data-Analytics-Core/genomics-lab-aws-calculator/issues](https://github.com/CSI-Genomics-and-Data-Analytics-Core/genomics-lab-aws-calculator/issues)
