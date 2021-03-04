import {Client} from "elasticsearch";
import ResolutionRequest from "./query/aggs/ResolutionRequest";
import {handleEsError} from "./EsErrorHandler";
import clone from "../util/clone";
import aggsAllAnnotations from "./query/aggs/aggs-all-annotations.json";
import {ERR_ES_AGGREGATE_LOCATION} from "../content/Placeholder";
import FilterAnnotationName from "./query/filter/FilterAnnotationName";
import FilterAnnotationValuePrefix from "./query/filter/FilterAnnotationValuePrefix";

/**
 * ElasticSearch Resolution Resource
 */
export default class ResolutionResource {

  private esClient: Client;
  private index: string;

  constructor(esClient: Client) {
    this.esClient = esClient;
    this.index = 'gnb-resolutions';
  }

  /**
   * Aggregate places from gnb-resolutions by name prefix
   */
  public async aggregateBy(
    prefix: string
  ): Promise<any> {
    const query = clone<any>(aggsAllAnnotations);

    const filters = query.nested_annotations.aggs.filter_annotations.filter.bool.must;
    filters.push(new FilterAnnotationName('plaats'));
    filters.push(new FilterAnnotationValuePrefix(prefix));

    const response = await this.esClient
      .search(new ResolutionRequest(query))
      .catch(e => handleEsError(e, ERR_ES_AGGREGATE_LOCATION));

    return response.aggregations.nested_annotations.filter_annotations.sum.buckets;
  }
}
