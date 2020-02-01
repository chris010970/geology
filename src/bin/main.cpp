
#include <opencv2/opencv.hpp>
#include <opencv2/core/core_c.h>

#include <iostream>
#include <iomanip>

using namespace cv;
using namespace std;

/*
input       : p x q x n multi-channel image.
targetMean  : n x 1 vector containing desired mean for each channel of the dstretched image. If empty, mean of the input data is used.
targetSigma : n x 1 vector containing desired sigma for each channel of the dstretched image. If empty, sigma of the input data is used.

returns floating point dstretched image
*/

Mat dstretch(Mat& input, Mat& targetMean, Mat& targetSigma)
{
   CV_Assert(input.channels() > 1);
 
   Mat dataMu, dataSigma, eigDataSigma, scale, stretch;

   Mat data = input.reshape(1, input.rows*input.cols);

   /*
   data stored as rows. 
   if x(i) = [xi1 xi2 .. xik]' is vector representing an input point, 
   data is now an N x k matrix:
   data = [x(1)' ; x(2)' ; .. ; x(N)']
   */

   // take the mean and standard deviation of input data
   meanStdDev(input, dataMu, dataSigma);

   /*
   perform PCA that gives us an eigenspace.
   eigenvectors matrix (R) lets us project input data into the new eigenspace.
   square root of eigenvalues gives us the standard deviation of projected data.
   */
   PCA pca(data, Mat(), CV_PCA_DATA_AS_ROW);

   /*
   prepare scaling (Sc) and strecthing (St) matrices.
   we use the relation var(a.X) = a^2.var(X) for a random variable X and 
   set
   scaling factor a = 1/(sigma of X) for diagonal entries of scaling matrix.
   stretching factor a = desired_sigma for diagonal entries of stretching matrix.
   */

   // scaling matrix (Sc)
   sqrt(pca.eigenvalues, eigDataSigma);
   scale = Mat::diag(1/eigDataSigma);

   // stretching matrix (St)
   // if targetSigma is empty, set sigma of transformed data equal to that of original data
   if (targetSigma.empty())
   {
      stretch = Mat::diag(dataSigma);
   }
   else
   {
      CV_Assert((1 == targetSigma.cols) &&  (1 == targetSigma.channels()) && 
         (input.channels() == targetSigma.rows));

      stretch = Mat::diag(targetSigma);
   }

   // convert to 32F
   stretch.convertTo(stretch, CV_32F);
 
   // subtract the mean from input data
   Mat zmudata;
   Mat repMu = repeat(dataMu.t(), data.rows, 1);

   subtract(data, repMu, zmudata, Mat(), CV_32F);

   // if targetMean is empty, set mean of transformed data equal to that of original data
   if (!targetMean.empty())
   {
      CV_Assert((1 == targetMean.cols) && (1 == targetMean.channels()) && 
         (input.channels() == targetMean.rows));

      repMu = repeat(targetMean.t(), data.rows, 1);

   }

   /*
   project zero mean data to the eigenspace, normalize the variance and reproject,
   then stretch it so that is has the desired sigma: StR'ScR(x(i) - mu), R'R = I.
   since the x(i)s are organized as rows in data, take the transpose of the above
   expression: (x(i)' - mu')R'Sc'(R')'St' = (x(i)' - mu')R'ScRSt,
   then add the desired mean:
   (x(i)' - mu')R'ScRSt + mu_desired
   */

   Mat a = pca.eigenvectors.t()*scale*pca.eigenvectors*stretch;
   
   Mat transformed = zmudata*(pca.eigenvectors.t()*scale*pca.eigenvectors*stretch);

   add(transformed, repMu, transformed, Mat(), CV_32F);

   // reshape transformed data
   Mat dstr32f = transformed.reshape(input.channels(), input.rows);

   return dstr32f;
}  


int main(int argc, char* argv[])
{
   // rgb image
   Mat bgr = imread(argv[1]);
   // target mean and sigma
   Mat mean = Mat::ones(3, 1, CV_32F) * 120;
   Mat sigma = Mat::ones(3, 1, CV_32F) * 100;


   // convert to CIE L*a*b* color space
   Mat lab;
   cvtColor(bgr, lab, COLOR_BGR2Lab);
   // dstretch Lab data. dstretch outputs a floating point matrix
   Mat dstrlab32f = dstretch(lab, mean, sigma);
   // convert to uchar
   Mat dstrlab8u;
   dstrlab32f.convertTo(dstrlab8u, CV_8UC3);



   // convert the stretched Lab image to rgb color space
   Mat dstrlab2bgr;
   cvtColor(dstrlab8u, dstrlab2bgr, COLOR_Lab2BGR);
   // dstretch RGB data
   Mat dstrbgr32f = dstretch(bgr, mean, sigma);


   // convert to uchar
   Mat dstrbgr8u;
   dstrbgr32f.convertTo(dstrbgr8u, CV_8UC3);


   imwrite( "dstrbgr32f.tif", dstrbgr32f );

   imwrite( argv[2], dstrbgr8u );
   imwrite( argv[3], dstrlab8u );

/*
   imshow("RGB", bgr);
   imshow("dstretched CIE L*a*b* converted to RGB", dstrlab2bgr);
   imshow("dstretched RGB", dstrbgr8u);
   waitKey();
*/
   return 0;
} 
