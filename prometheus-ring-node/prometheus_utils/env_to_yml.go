package main

import (
	"fmt"
	"os"
	"strings"
	"regexp"
	"gopkg.in/yaml.v3"
)

func main() {
	var outputFile string
	if len(os.Args) >= 2 {
		outputFile = os.Args[1]
	}else{
		outputFile = "/etc/prometheus/prometheus.yml"
	}
	fmt.Print("Output file: ", outputFile, "\n")

	// Fetch the YAML file from PROMETHEUS_YML environment variable
	var prometheus_yml interface{}
	var err error
	if prometheus_yml, err = fetchPrometheusConfig(); err != nil{
		fmt.Printf("Error reading variable: %v\n", err)
		os.Exit(1)
	}

	// Replace placeholders recursively
	if prometheus_yml, err = replacePlaceholders(prometheus_yml); err != nil{
		fmt.Printf("Error replacing environment variables: %v\n", err)
		os.Exit(1)
	}

	// Convert back to string
	prometheus_str, err := yaml.Marshal(prometheus_yml)
	if err != nil {
		fmt.Printf("Error marshaling YAML: %v\n", err)
		os.Exit(1)
	}

	// Output the result
	fmt.Println(string(prometheus_str))
	// err = os.WriteFile(outputFile, prometheus_str, 0644)
	// if err != nil {
	// 	fmt.Printf("Error writing to file: %v\n", err)
	// 	os.Exit(1)
	// }
}


// Fetches the prometheus config from PROMETHEUS_YML environment variable
func fetchPrometheusConfig() (interface{}, error) { // Corrected function
    yml_env := os.Getenv("PROMETHEUS_YML")
    if yml_env == "" {
        return nil, fmt.Errorf("PROMETHEUS_YML environment variable not set")
    }

    var yml_map interface{}
    err := yaml.Unmarshal([]byte(yml_env), &yml_map)
    if err != nil {
        return nil, fmt.Errorf("error unmarshalling YAML: %w", err)
    }

    return yml_map, nil
}

// Replaces placeholders in the YAML data with environment variables
func replacePlaceholders(data interface{}) (interface{}, error) {
	switch v := data.(type) {
	case map[string]interface{}:
		newMap := make(map[string]interface{})
		for key, value := range v {
			newValue, err := replacePlaceholders(value)
			if err != nil {
					return nil, err 
			}
			newMap[key] = newValue
		}
		return newMap, nil
	case []interface{}:
		newSlice := make([]interface{}, len(v))
		for i, item := range v {
			newItem, err := replacePlaceholders(item)
			if err != nil {
				return nil, err
			}
			newSlice[i] = newItem
		}
		return newSlice, nil
	case string:
		re := regexp.MustCompile(`{([A-Za-z0-9_]+)}`) // Matches {ENV_VAR}
		newString := v
		matches := re.FindAllStringSubmatch(v, -1)
		for _, match := range matches {
			if len(match) == 2 { // Ensure we have the full match and capture group
				placeHolder := match[1]
				envVarValue, err := treatPlaceHolder(placeHolder) // Keep the {} for treatPlaceHolder
				if err == nil { // Only replace if the variable is found
					newString = strings.ReplaceAll(newString, match[0], envVarValue)
				} else {
                    return "", fmt.Errorf("error replacing place holder %s: %v", placeHolder, err)
				}
			}
		}
		return newString, nil
	default:
		return v, nil
	}
}

func treatPlaceHolder(placeHolder string) (string, error) {
	switch placeHolder {
	case "HOSTNAME":
		hostName, err := os.Hostname()
		if err != nil {
			return "", fmt.Errorf("error getting hostname: %v", err)
		}
		return hostName, nil
	case "PROMETHEUS_YML":
		return "", fmt.Errorf("cannot use PROMETHEUS_YML as placeholder")
	default:
		envVar := os.Getenv(placeHolder)
		if envVar == "" {
			return "", fmt.Errorf("environment variable '%s' not found", placeHolder)
		}
		return envVar, nil
	}
}
