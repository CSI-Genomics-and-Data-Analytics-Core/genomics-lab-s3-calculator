# Cloud Cost Estimator

This cost calculator is tailored for Next-Generation Sequencing (NGS) data on the cloud, focusing on data storage and computational costs. It helps you estimate the expenses associated with storing and processing NGS data using AWS services, and contains information about data sizes and compute durations for approximation.

### Data Storage

Amazon Simple Storage Service (S3) is an object storage service devoted to secure storage, security, scalability, and performance.

Estimate the cost of storing your NGS data in AWS S3.

### Computational Costs

Amazon Elastic Compute Cloud (EC2) is a web service that provides resizable compute capacity in the cloud, allowing you to launch virtual servers (instances) with configurable CPU, memory, storage, and networking capacities, ideal for applications like processing Next-Generation Sequencing (NGS) data.

Calculate the expenses for processing NGS data using AWS EC2 instances and other computational resources.

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
shiny run
```
This will start the application, and you can access it in your web browser at http://localhost:8000.

### Export to Static Site Deployment

To export the project to a static site, run:

```sh
shinylive export . site
```
