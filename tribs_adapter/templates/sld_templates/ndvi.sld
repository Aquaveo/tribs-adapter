<?xml version="1.0" encoding="UTF-8"?>
<StyledLayerDescriptor version="1.0.0" 
    xsi:schemaLocation="http://www.opengis.net/sld StyledLayerDescriptor.xsd" 
    xmlns="http://www.opengis.net/sld" 
    xmlns:ogc="http://www.opengis.net/ogc" 
    xmlns:xlink="http://www.w3.org/1999/xlink" 
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <NamedLayer>
    <Name>tribs:ndvi_layer</Name>
    <UserStyle>
      <Title>Vegetation Fraction </Title>
      <FeatureTypeStyle>
        <Rule>
            <RasterSymbolizer>
                <ColorMap type="intervals">
                    <ColorMapEntry color="#FFFFFF" quantity="${env('ndvi_threshold', 0.1)}" opacity="0" />
                    <ColorMapEntry color="#ee0a08" quantity="${env('ndvi_max', 200)}" opacity="1.0" />
                </ColorMap>
            </RasterSymbolizer>
        </Rule>
      </FeatureTypeStyle>   
    </UserStyle>
  </NamedLayer>
</StyledLayerDescriptor>
